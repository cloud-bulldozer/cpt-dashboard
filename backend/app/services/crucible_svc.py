"""Service to pull data from a Crucible CDM OpenSearch data store

A set of helper methods to enable a project API to easily process data from a
Crucible controller's OpenSearch data backend.

This includes paginated, filtered, and sorted lists of benchmark runs, along
access to the associated Crucible documents such as iterations, samples, and
periods. Metric data can be accessed by breakout names, or aggregated by
breakout subsets or collection periods as either raw data points, statistical
aggregate, or Plotly graph format for UI display.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import time
from typing import Any, Iterator, Optional, Tuple, Union

from app import config
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException, status
from pydantic import BaseModel


class Metric(BaseModel):
    """Describe a single metric to be graphed or summarized

    This represents a JSON object provided by a caller through the
    get_multigraph or get_multisummary APIs to describe a specific
    metric.

    The default title (if the field is omitted) is the metric label with a
    suffix denoting breakout values selected, any unique parameter values
    in a selected iteration, and (if multiple runs are selected in any Graph
    list) an indication of the run index. For example,
    "mpstat::Busy-CPU [core=2,type=usr] (batch-size=16) {run 1}".

    Fields:
        run: run ID
        metric: the metric label, "ilab::train-samples-sec"
        aggregate: True to aggregate unspecified breakouts
        color: CSS color string ("green" or "#008000")
        names: Lock in breakouts
        periods: Select metrics for specific test period(s)
        title: Provide a title for the graph. The default is a generated title
    """

    run: str
    metric: str
    aggregate: bool = False
    color: Optional[str] = None
    names: Optional[list[str]] = None
    periods: Optional[list[str]] = None
    title: Optional[str] = None


class GraphList(BaseModel):
    """Describe a set of overlaid graphs

    This represents a JSON object provided by a caller through the get_graph
    API to introduce a set of constrained metrics to be graphed. The "run
    ID" here provides a default for the embedded Graph objects, and can be
    omitted if all Graph objects specify a run ID. (This is most useful to
    select a set of graphs all for a single run ID.)

    Normally the X axis will be the actual sample timestamp values; if you
    specify relative=True, the X axis will be the duration from the first
    timestamp of the metric series. This allows graphs of similar runs started
    at different times to be overlaid. Plotly (along with other plotting
    packages like PatternFly's Victory) doesn't support a "delta time" axis
    unit, so also specifying absolute_relative will report relative times as
    small absolute times (e.g., "1970-01-01 00:00:01" for 1 second) and a
    "tick format" of "%H:%M:%S", which will look nice on the graph as long as
    the total duration doesn't reach 24 hours. Without absolute_relative, the
    duration is reported as numeric (floating point) seconds.

    Fields:
        name: Specify a name for the set of graphs
        relative: True for relative timescale
        absolute_relative: True to report relative timestamps as absolute
        graphs: a list of Graph objects
    """

    name: str
    relative: bool = False
    absolute_relative: bool = False
    graphs: list[Metric]


@dataclass
class Point:
    """Graph point

    Record the start & end timestamp and value of a metric data point
    """

    begin: int
    end: int
    value: float


COLOR_NAMES = [
    "black",
    "aqua",
    "blue",
    "fuschia",
    "gray",
    "green",
    "maroon",
    "navy",
    "olive",
    "teal",
    "silver",
    "lightskyblue",
    "mediumspringgreen",
    "mistyrose",
    "darkgoldenrod",
    "cadetblue",
    "chocolate",
    "coral",
    "brown",
    "bisque",
    "deeppink",
    "sienna",
]


@dataclass
class Term:
    namespace: str
    key: str
    value: str


class Parser:
    """Help parsing filter expressions."""

    def __init__(self, term: str):
        """Construct an instance to help parse query parameter expressions

        These consist of a sequence of tokens separated by delimiters. Each
        token may be quoted to allow matching against strings with spaces.

        For example, `param:name="A string"`

        Args:
            term: A filter expression to parse
        """
        self.buffer = term
        self.context = term
        self.offset = 0

    def _next_token(
        self, delimiters: list[str] = [], optional: bool = False
    ) -> Tuple[str, Union[str, None]]:
        """Extract the next token from an expression

        Tokens may be quoted; the quotes are removed. for example, the two
        expressions `'param':"workflow"='"sdg"'` and `param:workflow:sdg` are
        identical.

        Args:
            delimiters: a list of delimiter characters
            optional: whether the terminating delimiter is optional

        Returns:
            A tuple consisting of the token and the delimiter (or None if
            parsing reached the end of the expression and the delimiter was
            optional)
        """

        @dataclass
        class Quote:
            open: int
            quote: str

        quoted: list[Quote] = []
        next_char = None
        token = ""
        first_quote = None
        for o in range(len(self.buffer)):
            next_char = self.buffer[o]
            if next_char in delimiters and not quoted:
                self.buffer = self.buffer[o + 1 :]
                self.offset += o + 1
                break
            elif next_char in ('"', "'"):
                if o == 0:
                    first_quote = next_char
                if quoted and quoted[-1].quote == next_char:
                    quoted.pop()
                else:
                    quoted.append(Quote(o, next_char))
            token += next_char
        else:
            next_char = None
            if quoted:
                q = quoted[-1]
                c = self.context
                i = q.open + self.offset
                annotated = c[:i] + "[" + c[i] + "]" + c[i + 1 :]
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"Unterminated quote at {annotated!r}"
                )

            # If delimiters are specified, and not optional, then we didn't
            # find one, and that's an error.
            if not optional and delimiters:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Missing delimiter from {','.join(delimiters)} after {token!r}",
                )
            self.buffer = ""
            self.offset = len(self.context)
        return (token, next_char) if not first_quote else (token[1:-1], next_char)


class CommonParams:
    """Help with sorting out parameters

    Parameter values are associated with iterations, but often a set of
    parameters is common across all iterations of a run, and that set can
    provide useful context.

    This helps to filter out identical parameters across a set of
    iterations.
    """

    def __init__(self):
        self.common: dict[str, Any] = {}
        self.omit = set()

    def add(self, params: dict[str, Any]):
        """Add a new iteration into the param set

        Mark all parameter keys which don't appear in all iterations, or which
        have different values in at least one iteration, to be omitted from the
        merged "common" param set.

        Args:
            params: the param dictionary of an iteration
        """
        if not self.common:
            self.common.update(params)
        else:
            for k, v in self.common.items():
                if k not in self.omit and (k not in params or v != params[k]):
                    self.omit.add(k)

    def render(self) -> dict[str, Any]:
        """Return a new param set with only common params"""
        return {k: v for k, v in self.common.items() if k not in self.omit}


class CrucibleService:
    """Support convenient generalized access to Crucible data

    This implements access to the "v7" Crucible "Common Data Model" through
    OpenSearch queries.
    """

    # OpenSearch massive limit on hits in a single query
    BIGQUERY = 262144

    # Define the 'run' document fields that support general filtering via
    # `?filter=<name>:<value>`
    #
    # TODO: this excludes 'desc', which isn't used by the ilab runs, and needs
    # different treatment as it's a text field rather than a term. It's not an
    # immediate priority for ilab, but may be important for general use.
    RUN_FILTERS = ("benchmark", "email", "name", "source", "harness", "host")

    # Define the keywords for sorting.
    DIRECTIONS = ("asc", "desc")
    FIELDS = (
        "begin",
        "benchmark",
        "desc",
        "email",
        "end",
        "harness",
        "host",
        "id",
        "name",
        "source",
    )

    # Set up a Logger at class level rather than at each instance creation
    formatter = logging.Formatter(
        "%(asctime)s %(process)d:%(thread)d %(levelname)s %(module)s:%(lineno)d %(message)s"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("CrucibleService")
    logger.addHandler(handler)

    # Set up a Logger at class level rather than at each instance creation
    formatter = logging.Formatter(
        "%(asctime)s %(process)d:%(thread)d %(levelname)s %(module)s:%(lineno)d %(message)s"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("CrucibleService")
    logger.addHandler(handler)

    def __init__(self, configpath: str = "crucible", version: int = 8):
        """Initialize a Crucible CDM (OpenSearch) connection.

        Generally the `configpath` should be scoped, like `ilab.crucible` so
        that multiple APIs based on access to distinct Crucible controllers can
        coexist.

        Initialization includes making an "info" call to confirm and record the
        server response.

        Args:
            configpath: The Vyper config path (e.g., "ilab.crucible")
        """
        self.cfg = config.get_config()
        self.user = self.cfg.get(configpath + ".username")
        self.password = self.cfg.get(configpath + ".password")
        self.auth = (self.user, self.password) if self.user or self.password else None
        self.url = self.cfg.get(configpath + ".url")
        self.set_cdm_version(version)
        self.elastic = AsyncElasticsearch(self.url, basic_auth=self.auth)
        self.logger.info("Initializing CDM V7 service to %s", self.url)

    def set_cdm_version(self, version):
        """Set up for a specific version of the CDM.

        We currently support v7 and v8. To dynamically select the latest CDM
        version active on an Opensearch instance, call detect_cdm() on a
        CrucibleService instance.
        """
        if version < 7 or version > 8:
            raise HTTPException(
                status_code=400,
                detail=f"The Crucible service supports CDM versions 7 and 8: {version} was specified",
            )
        self.logger.info(f"Selecting CDM version {version}")
        self.cdm_version = version
        self.id_names = {
            "run": "id" if version == 7 else "run-uuid",
            "iteration": "id" if version == 7 else "iteration-uuid",
            "period": "id" if version == 7 else "period-uuid",
            "sample": "id" if version == 7 else "sample-uuid",
            "metric_desc": "id" if version == 7 else "metric_desc-uuid",
        }

    async def detect_cdm(self):
        indices = await self.elastic.indices.get("cdmv*")
        versions = set()
        vpat = re.compile(r"cdmv(?P<version>\d+)dev-")
        for i in indices.keys():
            match = vpat.match(i)
            if match:
                try:
                    versions.add(int(match.group("version")))
                except Exception as e:
                    self.logger.debug(f"Skipping index {i}: {str(e)!r}")
        latest = max(versions)
        self.set_cdm_version(latest)

    def _get_index(self, root: str) -> str:
        return f"cdmv{self.cdm_version:d}dev-{root}"

    def _get_id_field(self, root: str) -> str:
        return self.id_names[root]

    @staticmethod
    def _get(source: dict[str, Any], fields: list[str], default: Optional[Any] = None):
        """Safely traverse nested dictionaries with a default value"""
        r = source
        last_missing = False
        for f in fields:
            last_missing = f not in r
            r = r.get(f, {})
        return default if last_missing else r

    @staticmethod
    def _split_list(alist: Optional[list[str]] = None) -> list[str]:
        """Split a list of parameters

        For simplicity, the APIs supporting "list" query parameters allow
        each element in the list to be a comma-separated list of strings.
        For example, ["a", "b", "c"] is logically the same as ["a,b,c"].

        This method normalizes the second form into first to simplify life for
        consumers.

        Args:
            alist: list of names or name lists

        Returns:
            A simple list of options
        """
        l: list[str] = []
        if alist:
            for n in alist:
                l.extend(n.split(","))
        return l

    @staticmethod
    def _normalize_date(value: Optional[Union[int, str, datetime]]) -> int:
        """Normalize date parameters

        The Crucible data model stores dates as string representations of an
        integer "millseconds-from-epoch" value. To allow flexibility, this
        Crucible service allows incoming dates to be specified as ISO-format
        strings, as integers, or as the stringified integer.

        That is, "2024-09-12 18:29:35.123000+00:00", "1726165775123", and
        1726165775123 are identical.

        Args:
            value: Representation of a date-time value

        Returns:
            The integer milliseconds-from-epoch equivalent
        """
        try:
            if isinstance(value, int):
                return value
            elif isinstance(value, datetime):
                return int(value.timestamp() * 1000.0)
            else:
                # If it's a stringified int, convert & return; otherwise try
                # to decode as a date string.
                try:
                    return int(value)
                except ValueError:
                    pass
                d = datetime.fromisoformat(value)
                return int(d.timestamp() * 1000.0)
        except Exception as e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Date representation {value} is not valid: {str(e)!r}",
            )

    @classmethod
    def _hits(
        cls, payload: dict[str, Any], fields: Optional[list[str]] = None
    ) -> Iterator[dict[str, Any]]:
        """Helper to iterate through OpenSearch query matches

        Iteratively yields the "_source" of each hit. As a convenience, can
        yield a sub-object of "_source" ... for example, specifying the
        optional "fields" as ["metric_desc", "id"] will yield the equivalent of
        hit["_source"]["metric_desc"]["id"]

        Args:
            payload: OpenSearch reponse payload
            fields: Optional sub-fields of "_source"

        Returns:
            Yields each object from the "greatest hits" list
        """
        if "hits" not in payload or not isinstance(payload["hits"], dict):
            raise HTTPException(
                status_code=500, detail=f"Attempt to iterate hits for {payload}"
            )
        hits = cls._get(payload, ["hits", "hits"], [])
        for h in hits:
            source = h["_source"]
            yield source if not fields else cls._get(source, fields)

    @classmethod
    def _aggs(
        cls, payload: dict[str, Any], aggregation: str
    ) -> Iterator[dict[str, Any]]:
        """Helper to access OpenSearch aggregations

        Iteratively yields the name and value of each aggregation returned
        by an OpenSearch query. This can also be used for nested aggregations
        by specifying an aggregation object.

        Args:
            payload: A JSON dict containing an "aggregations" field

        Returns:
            Yields each aggregation from an aggregation bucket list
        """
        if "aggregations" not in payload or not isinstance(
            payload["aggregations"], dict
        ):
            raise HTTPException(
                status_code=500,
                detail=f"Attempt to iterate missing aggregations for {payload}",
            )
        aggs = payload["aggregations"]
        if aggregation not in aggs or not isinstance(aggs[aggregation], dict):
            raise HTTPException(
                status_code=500,
                detail=f"Attempt to iterate missing aggregation {aggregation!r} for {payload}",
            )
        for agg in cls._get(aggs, [aggregation, "buckets"], []):
            yield agg

    @staticmethod
    def _format_timestamp(timestamp: Union[str, int]) -> str:
        """Convert stringified integer milliseconds-from-epoch to ISO date"""
        try:
            ts = int(timestamp)
        except Exception as e:
            CrucibleService.logger.warning(
                "invalid timestamp %r: %r", timestamp, str(e)
            )
            ts = 0
        return str(datetime.fromtimestamp(ts / 1000.00, timezone.utc))

    @classmethod
    def _format_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Helper to format a "metric_data" object

        Crucible stores the date, duration, and value as strings, so this
        converts them to more useful values. The end timestamp is converted
        to an ISO date-time string; the duration and value to floating point
        numbers.

        Args:
            data: a "metric_data" object

        Returns:
            A neatly formatted "metric_data" object
        """
        return {
            "begin": cls._format_timestamp(data["begin"]),
            "end": cls._format_timestamp(data["end"]),
            "duration": int(data["duration"]) / 1000,
            "value": float(data["value"]),
        }

    def _format_iteration(self, iteration: dict[str, Any]) -> dict[str, Any]:
        """Helper to format an "iteration" object

        Args:
            iteration: an "iteration" object

        Returns:
            A neatly formatted "iteration" object
        """
        iidn = self._get_id_field("iteration")
        return {
            "id": iteration[iidn],
            "num": iteration["num"],
            "path": iteration["path"],
            "primary_metric": iteration["primary-metric"],
            "primary_period": iteration["primary-period"],
            "status": iteration["status"],
        }

    def _format_period(self, period: dict[str, Any]) -> dict[str, Any]:
        """Helper to format a "period" object

        Crucible stores the date values as stringified integers, so this
        converts the begin and end timestamps to ISO date-time strings.

        Args:
            period: a "period" object

        Returns:
            A neatly formatted "period" object
        """
        pidn = self._get_id_field("period")
        return {
            "begin": self._format_timestamp(timestamp=period["begin"]),
            "end": self._format_timestamp(period["end"]),
            "id": period[pidn],
            "name": period["name"],
        }

    def _format_sample(self, sample: dict[str, Any]) -> dict[str, Any]:
        """Helper to format a "sample" object

        Args:
            sample: a "sample" object

        Returns:
            A neatly formatted "sample" object
        """
        sidn = self._get_id_field("sample")
        return {
            "num": sample["num"],
            "path": sample["path"],
            "id": sample[sidn],
            "status": sample["status"],
        }

    @classmethod
    def _build_filter_options(cls, filter: Optional[list[str]] = None) -> Tuple[
        Optional[list[dict[str, Any]]],
        Optional[list[dict[str, Any]]],
        Optional[list[dict[str, Any]]],
    ]:
        """Build filter terms for tag and parameter filter terms

        Each term has the form "<namespace>:<key><operator><value>". Any term
        may be quoted: quotes are stripped and ignored. (This is generally only
        useful on the <value> to include spaces.)

        We support three namespaces:
            param: Match against param index arg/val
            tag: Match against tag index name/val
            run: Match against run index fields

        We support two operators:
            =: Exact match
            ~: Partial match

        Args:
            filter: list of filter terms like "param:key=value"

        Returns:
            A set of OpenSearch filter object lists to detect missing
            and matching documents for params, tags, and run fields. For
            example, to select param:batch-size=12 results in the
            following param filter list:

                [
                    {'
                        dis_max': {
                            'queries': [
                                {
                                    'bool': {
                                        'must': [
                                            {'term': {'param.arg': 'batch-size'}},
                                            {'term': {'param.val': '12'}}
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ]
        """
        terms = defaultdict(list)
        for term in cls._split_list(filter):
            p = Parser(term)
            namespace, _ = p._next_token([":"])
            key, operation = p._next_token(["=", "~"])
            value, _ = p._next_token()
            if operation == "~":
                value = f".*{value}.*"
                matcher = "regexp"
            else:
                matcher = "term"
            if namespace in ("param", "tag"):
                if namespace == "param":
                    key_field = "param.arg"
                    value_field = "param.val"
                else:
                    key_field = "tag.name"
                    value_field = "tag.val"
                terms[namespace].append(
                    {
                        "bool": {
                            "must": [
                                {"term": {key_field: key}},
                                {matcher: {value_field: value}},
                            ]
                        }
                    }
                )
            elif namespace == "run":
                terms[namespace].append({matcher: {f"run.{key}": value}})
            else:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"unknown filter namespace {namespace!r}",
                )
        param_filter = None
        tag_filter = None
        if "param" in terms:
            param_filter = [{"dis_max": {"queries": terms["param"]}}]
        if "tag" in terms:
            tag_filter = [{"dis_max": {"queries": terms["tag"]}}]
        return param_filter, tag_filter, terms.get("run")

    @classmethod
    def _build_name_filters(
        cls, namelist: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Build filter terms for metric breakout names

        for example, "cpu=10" filters for metric data descriptors where the
        breakout name "cpu" exists and has a value of 10.

        Args:
            namelist: list of possibly comma-separated list values

        Returns:
            A list of filters to match breakout terms
        """
        names: list[str] = cls._split_list(namelist)
        filters = []
        for e in names:
            try:
                n, v = e.split("=", maxsplit=1)
            except ValueError:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"Filter item {e!r} must be '<k>=<v>'"
                )
            filters.append({"term": {f"metric_desc.names.{n}": v}})
        return filters

    def _build_period_filters(
        self, periodlist: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Build period filters

        Generate metric_desc filter terms to match against a list of period IDs.

        Note that not all metric descriptions are periodic, and we don't want
        these filters to exclude them -- so the filter will exclude only
        documents that have a period and don't match. (That is, we won't drop
        any non-periodic metrics. We expect those to be filtered by timestamp
        instead.)

        Args:
            period: list of possibly comma-separated period IDs

        Returns:
            A filter term that requires a period.id match only for metric_desc
            documents with a period.
        """
        pl: list[str] = self._split_list(periodlist)
        pidn = self._get_id_field("period")
        if pl:
            return [
                {
                    "dis_max": {
                        "queries": [
                            {"bool": {"must_not": {"exists": {"field": "period"}}}},
                            {"terms": {f"period.{pidn}": pl}},
                        ]
                    }
                }
            ]
        else:
            return []

    def _build_metric_filters(
        self,
        run: str,
        metric: str,
        names: Optional[list[str]] = None,
        periods: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Helper for filtering metric descriptions

        We normally filter by run, metric "label", and optionally by breakout
        names and periods. This encapsulates the filter construction.

        Args:
            run: run ID
            metric: metric label (ilab::sdg-samples-sec)
            names: list of "name=value" filters
            periods: list of period IDs

        Returns:
            A list of OpenSearch filter expressions
        """
        msource, mtype = metric.split("::")
        ridn = self._get_id_field("run")
        return (
            [
                {"term": {f"run.{ridn}": run}},
                {"term": {"metric_desc.source": msource}},
                {"term": {"metric_desc.type": mtype}},
            ]
            + self._build_name_filters(names)
            + self._build_period_filters(periods)
        )

    @classmethod
    def _build_sort_terms(cls, sorters: Optional[list[str]]) -> list[dict[str, Any]]:
        """Build sort term list

        Sorters may reference any native `run` index field and must specify
        either "asc"(ending) or "desc"(ending) sort order. Any number of
        sorters may be combined, like ["name:asc,benchmark:desc", "end:desc"]

        Args:
            sorters: list of <key>:<direction> sort terms

        Returns:
            list of OpenSearch sort terms
        """
        if sorters:
            sort_terms = []
            for s in sorters:
                key, dir = s.split(":", maxsplit=1)
                if dir not in cls.DIRECTIONS:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Sort direction {dir!r} must be one of {','.join(cls.DIRECTIONS)}",
                    )
                if key not in cls.FIELDS:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Sort key {key!r} must be one of {','.join(cls.FIELDS)}",
                    )
                sort_terms.append({f"run.{key}": {"order": dir}})
        else:
            sort_terms = [{"run.begin": {"order": "asc"}}]
        return sort_terms

    async def _search(
        self, index: str, query: Optional[dict[str, Any]] = None, **kwargs
    ) -> dict[str, Any]:
        """Issue an OpenSearch query

        Args:
            index: The "base" CDM index name, e.g., "run", "metric_desc"
            query: An OpenSearch query object
            kwargs: Additional OpenSearch parameters

        Returns:
            The OpenSearch response payload (JSON dict)
        """
        idx = self._get_index(index)
        start = time.time()
        value = await self.elastic.search(index=idx, body=query, **kwargs)
        self.logger.info(
            "QUERY on %s took %.3f seconds, hits: %d",
            idx,
            time.time() - start,
            value.get("hits", {}).get("total"),
        )
        return value

    async def close(self):
        """Close the OpenSearch connection"""
        if self.elastic:
            await self.elastic.close()
        self.elastic = None

    async def search(
        self,
        index: str,
        filters: Optional[list[dict[str, Any]]] = None,
        aggregations: Optional[dict[str, Any]] = None,
        sort: Optional[list[dict[str, str]]] = None,
        source: Optional[str] = None,
        size: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """OpenSearch query helper

        Combine index, filters, aggregations, sort, and pagination options
        into an OpenSearch query.

        Args:
            index: "root" CDM index name ("run", "metric_desc", ...)
            filters: list of JSON dict filter terms {"term": {"name": "value}}
            aggregations: list of JSON dict aggregations {"name": {"term": "name"}}
            sort: list of JSON dict sort terms ("name": "asc")
            size: The number of hits to return; defaults to "very large"
            offset: The number of hits to skip, for pagination
            kwargs: Additional OpenSearch options

        Returns:
            The OpenSearch response
        """
        f = filters if filters else []
        query = {
            "size": self.BIGQUERY if size is None else size,
            "query": {"bool": {"filter": f}},
        }
        if sort:
            query.update({"sort": sort})
        if source:
            query.update({"_source": source})
        if offset:
            query.update({"from": offset})
        if aggregations:
            query.update({"aggs": aggregations})
        return await self._search(index, query, **kwargs)

    async def _get_metric_ids(
        self,
        run: str,
        metric: str,
        namelist: Optional[list[str]] = None,
        periodlist: Optional[list[str]] = None,
        aggregate: bool = False,
    ) -> list[str]:
        """Generate a list of matching metric_desc IDs

        Given a specific run and metric name, and a set of breakout filters,
        returns a list of metric desc IDs that match.

        If a single ID is required to produce a consistent metric, and the
        supplied filters produce more than one without aggregation, raise a
        422 HTTP error (UNPROCESSABLE CONTENT) with a response body showing
        the unsatisfied breakouts (name and available values).

        TODO: Instead of either single metric or aggregation across multiple
        metrics, we should support "breakouts", which would individually
        process (graph, summarize, or list) data for each "loose" breakout
        name. E.g., Busy-CPU might list per-core, or per-processor mode.

        Args:
            run: run ID
            metric: combined metric name (e.g., sar-net::packets-sec)
            namelist: a list of breakout filters like "type=physical"
            periodlist: a list of period IDs
            aggregate: if True, allow multiple metric IDs

        Returns:
            A list of matching metric_desc ID value(s)
        """
        filters = self._build_metric_filters(run, metric, namelist, periodlist)
        metrics = await self.search(
            "metric_desc",
            filters=filters,
            ignore_unavailable=True,
        )
        if len(metrics["hits"]["hits"]) < 1:
            self.logger.info(f"No metric descs: filters={filters}")
            return []
        mdidn = self._get_id_field("metric_desc")
        ids = [h["metric_desc"][mdidn] for h in self._hits(metrics)]
        if len(ids) < 2 or aggregate:
            return ids

        # If we get here, the client asked for breakout data that doesn't
        # resolve to a single metric stream, and didn't specify aggregation.
        # Offer some help.
        names = defaultdict(set)
        periods = set()
        response = {
            "message": f"More than one metric ({len(ids)}) means "
            "you should add breakout filters or aggregate."
        }
        pidn = self._get_id_field("period")
        for m in self._hits(metrics):
            if "period" in m:
                periods.add(m["period"][pidn])
            for n, v in m["metric_desc"]["names"].items():
                names[n].add(v)

        # We want to help filter a consistent summary, so only show those
        # breakout names with more than one value.
        response["names"] = {n: sorted(v) for n, v in names.items() if v and len(v) > 1}
        response["periods"] = sorted(periods)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=response
        )

    async def _build_timestamp_range_filters(
        self, periods: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Create a timestamp range filter

        This extracts the begin and end timestamps from the list of periods and
        builds a timestamp filter range to select documents on or after the
        earliest begin timestamp and on or before the latest end timestamp.

        Args:
            periods: a list of CDM period IDs

        Returns:
            Constructs a range filter for the earliest begin timestamp and the
            latest end timestamp among the specified periods.
        """

        if periods:
            ps = self._split_list(periods)
            pidn = self._get_id_field("period")
            matches = await self.search(
                "period", filters=[{"terms": {f"period.{pidn}": ps}}]
            )
            try:
                start = min([int(h) for h in self._hits(matches, ["period", "begin"])])
                end = max([int(h) for h in self._hits(matches, ["period", "end"])])
            except Exception as e:
                plist = ",".join(ps)
                self.logger.warning(
                    (
                        "Can't compute a time filter because one of the periods "
                        f"in {plist!r} is missing a timestamp: {str(e)!r}"
                    )
                )
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    (
                        "Cannot process metric time filter: at least one of "
                        f"the periods in {plist!r} is broken and lacks a time range."
                    ),
                )
            return [
                {"range": {"metric_data.begin": {"gte": str(start)}}},
                {"range": {"metric_data.end": {"lte": str(end)}}},
            ]
        else:
            return []

    async def _get_run_ids(
        self, index: str, filters: Optional[list[dict[str, Any]]] = None
    ) -> set[str]:
        """Return a set of run IDs matching a filter

        Documents in the specified index must have ID fields. This returns
        a set of unique run IDs matched by the filter in the specified index.

        Args:
            index: root CDM index name
            filters: a list of OpenSearch filter terms

        Returns:
            a set of unique run ID values
        """
        ridn = self._get_id_field("run")
        filtered = await self.search(
            index, source=f"run.{ridn}", filters=filters, ignore_unavailable=True
        )
        self.logger.debug("HITS: %s", filtered["hits"]["hits"])
        return set([x for x in self._hits(filtered, ["run", "id"])])

    async def _make_title(
        self,
        run_id: str,
        run_id_list: list[str],
        metric_item: Metric,
        params_by_run: dict[str, Any],
        periods_by_run: dict[str, Any],
    ) -> str:
        """Compute a default title for a graph

        Use the period, breakout name selections, run list, and iteration
        parameters to construct a meaningful name for a metric.

        For example, "ilab::sdg-samples-sec (batch-size=4) {run 1}", or
        "mpstat::Busy-CPU [cpu=4]"

        Args:
            run_id: the Crucible run ID
            run_id_list: ordered list of run IDs in our list of metrics
            metric_item: the current MetricItem object
            periods: list of aggregation periods, if any
            params_by_run: initially empty dict used to cache parameters
            periods_by_run: initially empty dict used to cache periods

        Returns:
            A string title
        """
        names = metric_item.names
        ridn = self._get_id_field("run")
        iidn: str = self._get_id_field("iteration")
        pidn = self._get_id_field("period")
        metric = metric_item.metric
        if metric_item.periods and len(metric_item.periods) == 1:
            period = metric_item.periods[0]
        else:
            period = None
        if run_id not in params_by_run:
            # Gather iteration parameters outside the loop for help in
            # generating useful labels.
            all_params = await self.search(
                "param", filters=[{"term": {f"run.{ridn}": run_id}}]
            )
            collector = defaultdict(defaultdict)
            for h in self._hits(all_params):
                collector[h["iteration"][iidn]][h["param"]["arg"]] = h["param"]["val"]
            params_by_run[run_id] = collector
        else:
            collector = params_by_run[run_id]

        if run_id not in periods_by_run:
            periods = await self.search(
                "period", filters=[{"term": {f"run.{ridn}": run_id}}]
            )
            iteration_periods = defaultdict(list[dict[str, Any]])
            for p in self._hits(periods):
                iteration_periods[p["iteration"][iidn]].append(p["period"])
            periods_by_run[run_id] = iteration_periods
        else:
            iteration_periods = periods_by_run[run_id]

        # We can easily end up with multiple graphs across distinct
        # periods or iterations, so we want to be able to provide some
        # labeling to the graphs. We do this by looking for unique
        # iteration parameters values, since the iteration number and
        # period name aren't useful by themselves.
        name_suffix = ""
        if metric_item.periods:
            iteration = None
            for i, plist in iteration_periods.items():
                if set(metric_item.periods) <= set([p[pidn] for p in plist]):
                    iteration = i
                if period:
                    for p in plist:
                        if p[pidn] == period:
                            name_suffix += f" {p['name']}"

            # If the period(s) we're graphing resolve to a single
            # iteration in a run with multiple iterations, then we can
            # try to find a unique title suffix based on distinct param
            # values for that iteration.
            if iteration and len(collector) > 1:
                unique = collector[iteration].copy()
                for i, params in collector.items():
                    if i != iteration:
                        for p in list(unique.keys()):
                            if p in params and unique[p] == params[p]:
                                del unique[p]
                if unique:
                    name_suffix += (
                        " (" + ",".join([f"{p}={v}" for p, v in unique.items()]) + ")"
                    )

        if len(run_id_list) > 1:
            name_suffix += f" {{run {run_id_list.index(run_id) + 1}}}"

        options = (" [" + ",".join(names) + "]") if names else ""
        return metric + options + name_suffix

    async def get_run_filters(self) -> dict[str, dict[str, list[str]]]:
        """Return possible tag and filter terms

        Return a description of tag and param filter terms meaningful
        across all datasets. TODO: we should support date-range and benchmark
        filtering. Consider supporting all `run` API filtering, which would
        allow adjusting the filter popups to drop options no longer relevant
        to a given set.

            {
                "param": {
                    {"gpus": [4", "8"]}
                }
            }

        Returns:
            A two-level JSON dict; the first level is the namespace (param or
            tag), the second level key is the param/tag/field name and its value
            is the set of values defined for that key.
        """
        tags = await self.search(
            "tag",
            size=0,
            aggregations={
                "key": {
                    "terms": {"field": "tag.name", "size": self.BIGQUERY},
                    "aggs": {
                        "values": {"terms": {"field": "tag.val", "size": self.BIGQUERY}}
                    },
                }
            },
            ignore_unavailable=True,
        )
        params = await self.search(
            "param",
            size=0,
            aggregations={
                "key": {
                    "terms": {"field": "param.arg", "size": self.BIGQUERY},
                    "aggs": {
                        "values": {
                            "terms": {"field": "param.val", "size": self.BIGQUERY}
                        }
                    },
                }
            },
            ignore_unavailable=True,
        )
        aggs = {
            k: {"terms": {"field": f"run.{k}", "size": self.BIGQUERY}}
            for k in self.RUN_FILTERS
        }
        runs = await self.search(
            "run",
            size=0,
            aggregations=aggs,
        )
        result = defaultdict(lambda: defaultdict(lambda: set()))
        for p in self._aggs(params, "key"):
            for v in p["values"]["buckets"]:
                result["param"][p["key"]].add(v["key"])
        for t in self._aggs(tags, "key"):
            for v in t["values"]["buckets"]:
                result["tag"][t["key"]].add(v["key"])
        for name in self.RUN_FILTERS:
            for f in self._aggs(runs, name):
                result["run"][name].add(f["key"])
        return {s: {k: list(v) for k, v in keys.items()} for s, keys in result.items()}

    async def get_runs(
        self,
        filter: Optional[list[str]] = None,
        start: Optional[Union[int, str, datetime]] = None,
        end: Optional[Union[int, str, datetime]] = None,
        offset: int = 0,
        sort: Optional[list[str]] = None,
        size: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Return matching Crucible runs

        Filtered and sorted list of runs.

        {
            "sort": [],
            "startDate": "2024-01-01T05:00:00+00:00",
            "size": 1,
            "offset": 0,
            "results": [
                {
                    "begin": "1722878906342",
                    "benchmark": "ilab",
                    "email": "A@email",
                    "end": "1722880503544",
                    "id": "4e1d2c3c-b01c-4007-a92d-23a561af2c11",
                    "name": "\"A User\"",
                    "source": "node.example.com//var/lib/crucible/run/ilab--2024-08-05_17:17:13_UTC--4e1d2c3c-b01c-4007-a92d-23a561af2c11",
                    "tags": {
                        "topology": "none"
                    },
                    "iterations": [
                        {
                            "iteration": 1,
                            "primary_metric": "ilab::train-samples-sec",
                            "primary_period": "measurement",
                            "status": "pass",
                            "params": {
                                "cpu-offload-pin-memory": "1",
                                "model": "/home/models/granite-7b-lab/",
                                "data-path": "/home/data/training/knowledge_data.jsonl",
                                "cpu-offload-optimizer": "1",
                                "nnodes": "1",
                                "nproc-per-node": "4",
                                "num-runavg-samples": "2"
                            }
                        }
                    ],
                    "primary_metrics": [
                        "ilab::train-samples-sec"
                    ],
                    "status": "pass",
                    "params": {
                        "cpu-offload-pin-memory": "1",
                        "model": "/home/models/granite-7b-lab/",
                        "data-path": "/home/data/training/knowledge_data.jsonl",
                        "cpu-offload-optimizer": "1",
                        "nnodes": "1",
                        "nproc-per-node": "4",
                        "num-runavg-samples": "2"
                    },
                    "begin_date": "2024-08-05 17:28:26.342000+00:00",
                    "end_date": "2024-08-05 17:55:03.544000+00:00"
                }
            ],
            "count": 1,
            "total": 15,
            "next_offset": 1
        }

        Args:
            start: Include runs starting at timestamp
            end: Include runs ending no later than timestamp
            filter: List of tag/param filter terms (parm:key=value)
            sort: List of sort terms (column:<dir>)
            size: Include up to <size> runs in output
            offset: Use size/from pagination instead of search_after

        Returns:
            JSON object with "results" list and "housekeeping" fields
        """

        # We need to remove runs which don't match against 'tag' or 'param'
        # filter terms. The CDM schema doesn't make it possible to do this in
        # one shot. Instead, we run queries against the param and tag indices
        # separately, producing a list of run IDs which we'll exclude from the
        # final collection.
        #
        # If there are no matches, we can exit early. (TODO: should this be an
        # error, or just a success with an empty list?)
        results = {}
        filters = []
        sorters = self._split_list(sort)
        results["sort"] = sorters
        sort_terms = self._build_sort_terms(sorters)
        param_filters, tag_filters, run_filters = self._build_filter_options(filter)
        if run_filters:
            filters.extend(run_filters)
        if start or end:
            self.logger.info(f"Filtering runs from {start} to {end}")
            s = None
            e = None
            if start:
                s = self._normalize_date(start)
                results["startDate"] = datetime.fromtimestamp(
                    s / 1000.0, tz=timezone.utc
                ).isoformat()
            if end:
                e = self._normalize_date(end)
                results["endDate"] = datetime.fromtimestamp(
                    e / 1000.0, tz=timezone.utc
                ).isoformat()

            if s and e and s > e:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Invalid date format, start_date must be less than end_date"
                    },
                )
            cond = {}
            if s:
                cond["gte"] = str(s)
            if e:
                cond["lte"] = str(e)
            filters.append({"range": {"run.begin": cond}})
        if size:
            results["size"] = size
        results["offset"] = offset if offset is not None else 0

        # In order to filter by param or tag values, we need to produce a list
        # of matching RUN IDs from each index. We'll then drop any RUN ID that's
        # not on both lists.
        if tag_filters:
            tagids = await self._get_run_ids("tag", tag_filters)
        if param_filters:
            paramids = await self._get_run_ids("param", param_filters)

        # If it's obvious we can't produce any matches at this point, exit.
        if (tag_filters and len(tagids) == 0) or (param_filters and len(paramids) == 0):
            results.update({"results": [], "count": 0, "total": 0})
            return results

        hits = await self.search(
            "run",
            size=size,
            offset=offset,
            sort=sort_terms,
            filters=filters,
            **kwargs,
            ignore_unavailable=True,
        )
        rawiterations = await self.search("iteration", ignore_unavailable=True)
        rawtags = await self.search("tag", ignore_unavailable=True)
        rawparams = await self.search("param", ignore_unavailable=True)

        # NOTE: CDM considers run timestamps "informational" and uses period
        # timestamps if necessary to replace them. We could delay this call
        # until (if) we find a "broken" run, and potentially even make separate
        # queries based on run ID.
        rawperiods = await self.search(index="period", ignore_unavailable=True)

        iterations = defaultdict(list)
        periods: dict[str, tuple[int, int]] = {}
        tags = defaultdict(defaultdict)
        params = defaultdict(defaultdict)
        run_params = defaultdict(list)
        ridn = self._get_id_field("run")
        iidn = self._get_id_field("iteration")

        for i in self._hits(rawiterations):
            iterations[i["run"][ridn]].append(i["iteration"])

        # Organize tags by run ID
        for t in self._hits(rawtags):
            tags[t["run"][ridn]][t["tag"]["name"]] = t["tag"]["val"]

        # Organize period timestamps by run ID
        for p in self._hits(rawperiods):
            period = p["period"]
            rid = p["run"][ridn]
            range = periods.get(rid)
            try:
                b = int(period["begin"])
                e = int(period["end"])
            except Exception as e:
                self.logger.warning(f"bad timestamp in period {period}: {str(e)!r}")
                continue
            if range:
                range = (min(range[0], b), max(range[1], e))
            else:
                range = (b, e)
            periods[rid] = range

        # Organize params by iteration ID
        for p in self._hits(rawparams):
            run_params[p["run"][ridn]].append(p)
            params[p["iteration"][iidn]][p["param"]["arg"]] = p["param"]["val"]

        runs = {}
        for h in self._hits(hits):
            run = h["run"]
            rid = run[ridn]

            # Filter the runs by our tag and param queries
            if param_filters and rid not in paramids:
                continue

            if tag_filters and rid not in tagids:
                continue

            # Convert string timestamps (milliseconds from epoch) to int.
            # If the run document has no begin or end, look for the periods
            b = None
            e = None
            if run.get("begin") and run.get("end"):
                try:
                    b = int(run["begin"])
                    e = int(run["end"])
                except Exception as exc:
                    self.logger.warning(f"bad timestamps in run {run}: {str(exc)!r}")
            if (b is None or e is None) and rid in periods:
                b, e = periods[rid]
            if b is None or e is None:
                self.logger.warning(
                    f"can't find begin/end timestamps for run {rid}: ignoring"
                )
                continue
            run["begin"] = b
            run["end"] = e

            # Always normalize the Crucible RUN ID field to "id" regardless
            # of the CDM version, for client consistency.
            if ridn != "id":
                run["id"] = rid
                del run[ridn]
            run["tags"] = tags.get(rid, {})
            run["iterations"] = []
            run["primary_metrics"] = set()
            common = CommonParams()

            # Collect unique iterations: the status is "fail" if any iteration
            # for that run ID failed.
            for i in iterations.get(rid, []):
                iparams = params.get(i[iidn], {})
                if "status" not in run:
                    run["status"] = i["status"]
                else:
                    if i["status"] != "pass":
                        run["status"] = i["status"]
                common.add(iparams)
                run["primary_metrics"].add(i["primary-metric"])
                run["iterations"].append(
                    {
                        "iteration": i["num"],
                        "primary_metric": i["primary-metric"],
                        "primary_period": i["primary-period"],
                        "status": i["status"],
                        "params": iparams,
                    }
                )
            run["iterations"].sort(key=lambda i: i["iteration"])
            run["params"] = common.render()
            try:
                run["begin_date"] = self._format_timestamp(run["begin"])
                run["end_date"] = self._format_timestamp(run["end"])
            except KeyError as e:
                self.logger.warning("Missing 'run' key %r in %s", str(e), run)
                run["begin_date"] = self._format_timestamp("0")
                run["end_date"] = self._format_timestamp("0")

            runs[rid] = run

        count = len(runs)
        total = hits["hits"]["total"]["value"]
        results.update(
            {
                "results": list(runs.values()),
                "count": count,
                "total": total,
            }
        )
        if size and (offset + count < total):
            results["next_offset"] = offset + size
        return results

    async def get_tags(self, run: str, **kwargs) -> dict[str, str]:
        """Return the set of tags associated with a run

        Args:
            run: run ID

        Returns:
            JSON dict with "tag" keys showing each value
        """
        ridn = self._get_id_field("run")
        tags = await self.search(
            index="tag",
            filters=[{"term": {f"run.{ridn}": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        return {t["name"]: t["val"] for t in self._hits(tags, ["tag"])}

    async def get_params(
        self, run: Optional[str] = None, iteration: Optional[str] = None, **kwargs
    ) -> dict[str, dict[str, str]]:
        """Return the set of parameters for a run or iteration

        Parameters are technically associated with an iteration, but can be
        aggregated for a run. This will return a set of parameters for each
        iteration; plus, if a "run" was specified, a filtered list of param
        values that are common across all iterations.

        Args:
            run: run ID
            iteration: iteration ID
            kwargs: additional OpenSearch keywords

        Returns:
            JSON dict of param values by iteration (plus "common" if by run ID)
        """
        if not run and not iteration:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "A params query requires either a run or iteration ID",
            )
        ridn = self._get_id_field("run")
        iidn = self._get_id_field("iteration")
        match = {
            f"run.{ridn}" if run else f"iteration.{iidn}": run if run else iteration
        }
        params = await self.search(
            index="param",
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        response = defaultdict(defaultdict)
        for param in self._hits(params):
            iter = param["iteration"][iidn]
            arg = param["param"]["arg"]
            val = param["param"]["val"]
            old = self._get(response, [iter, arg])
            if old:
                self.logger.warning(
                    "Duplicate param %s for iteration %s (%r, %r)", arg, iter, old, val
                )
            response[iter][arg] = val

        # Filter out all parameter values that don't exist in all or which have
        # different values.
        if run:
            common = CommonParams()
            for params in response.values():
                common.add(params)
            response["common"] = common.render()
        return response

    async def get_iterations(self, run: str, **kwargs) -> list[dict[str, Any]]:
        """Return a list of iterations for a run

        Args:
            run: run ID
            kwargs: additional OpenSearch keywords

        Returns:
            A list of iteration documents
        """
        ridn = self._get_id_field("run")
        iidn = self._get_id_field("iteration")
        hits = await self.search(
            index="iteration",
            filters=[{"term": {f"run.{ridn}": run}}],
            sort=[{"iteration.num": "asc"}],
            **kwargs,
            ignore_unavailable=True,
        )

        iterations = []
        for i in self._hits(hits, ["iteration"]):
            iterations.append(self._format_iteration(i))
        return iterations

    async def get_samples(
        self, run: Optional[str] = None, iteration: Optional[str] = None, **kwargs
    ):
        """Return a list of samples for a run or iteration

        Args:
            run: run ID
            iteration: iteration ID
            kwargs: additional OpenSearch keywords

        Returns:
            A list of sample documents.
        """
        if not run and not iteration:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "A sample query requires either a run or iteration ID",
            )
        ridn = self._get_id_field("run")
        iidn = self._get_id_field("iteration")
        match = {
            f"run.{ridn}" if run else f"iteration.{iidn}": run if run else iteration
        }
        hits = await self.search(
            index="sample",
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        samples = []
        for s in self._hits(hits):
            sample = self._format_sample(s["sample"])
            sample["iteration"] = s["iteration"]["num"]
            sample["primary_metric"] = s["iteration"]["primary-metric"]
            sample["primary_period"] = s["iteration"]["primary-period"]
            samples.append(sample)
        return samples

    async def get_periods(
        self,
        run: Optional[str] = None,
        iteration: Optional[str] = None,
        sample: Optional[str] = None,
        **kwargs,
    ):
        """Return a list of periods associated with a run, an iteration, or a
        sample

        The "period" document is normalized to represent timestamps using ISO
        strings.

        Args:
            run: run ID
            iteration: iteration ID
            sample: sample ID
            kwargs: additional OpenSearch parameters

        Returns:
            a list of normalized period documents
        """
        if not any((run, iteration, sample)):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "A period query requires a run, iteration, or sample ID",
            )
        match = None
        ridn = self._get_id_field("run")
        iidn = self._get_id_field("iteration")
        sidn = self._get_id_field("sample")
        if sample:
            match = {f"sample.{sidn}": sample}
        elif iteration:
            match = {f"iteration.{iidn}": iteration}
        else:
            match = {f"run.{ridn}": run}
        periods = await self.search(
            index="period",
            filters=[{"term": match}],
            sort=[{"period.begin": "asc"}],
            **kwargs,
            ignore_unavailable=True,
        )
        body = []
        for h in self._hits(periods):
            period = self._format_period(period=h["period"])
            period["iteration"] = h["iteration"]["num"]
            period["sample"] = h["sample"]["num"]
            is_primary = h["iteration"]["primary-period"] == h["period"]["name"]
            period["is_primary"] = is_primary
            if is_primary:
                period["primary_metric"] = h["iteration"]["primary-metric"]
            period["status"] = h["iteration"]["status"]
            body.append(period)
        return body

    async def get_metrics_list(self, run: str, **kwargs) -> dict[str, Any]:
        """Return a list of metrics available for a run

        Each run may have multiple performance metrics stored. This API allows
        retrieving a sorted list of the metrics available for a given run, with
        the "names" selection criteria available for each and, for "periodic"
        (benchmark) metrics, the defined periods for which data was gathered.

        {
            "ilab::train-samples-sec": {
                "periods": [{"id": <id>, "name": "measurement"}],
                "breakouts": {"benchmark-group" ["unknown"], ...}
            },
            "iostat::avg-queue-length": {
                "periods": [],
                "breakouts": {"benchmark-group": ["unknown"], ...},
            },
            ...
        }

        Args:
            run: run ID

        Returns:
            List of metrics available for the run
        """
        ridn = self._get_id_field("run")
        hits = await self.search(
            index="metric_desc",
            filters=[{"term": {f"run.{ridn}": run}}],
            ignore_unavailable=True,
            **kwargs,
        )
        met = {}
        pidn = self._get_id_field("period")
        for h in self._hits(hits):
            desc = h["metric_desc"]
            name = desc["source"] + "::" + desc["type"]
            if name in met:
                record = met[name]
            else:
                record = {"periods": [], "breakouts": defaultdict(list)}
                met[name] = record
            if "period" in h:
                record["periods"].append(h["period"][pidn])
            for n, v in desc["names"].items():
                # mimic a set, since the set type doesn't serialize
                if v not in record["breakouts"][n]:
                    record["breakouts"][n].append(v)
        return met

    async def get_metric_breakouts(
        self,
        run: str,
        metric: str,
        names: Optional[list[str]] = None,
        periods: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Help explore available metric breakouts

        Args:
            run: run ID
            metric: metric label (e.g., "mpstat::Busy-CPU")
            names: list of name filters ("cpu=3")
            periods: list of period IDs

        Returns:
            A description of all breakout names and values, which can be
            specified to narrow down metrics returns by the data, summary, and
            graph APIs.

            {
                "label": "mpstat::Busy-CPU",
                "class": [
                    "throughput"
                ],
                "type": "Busy-CPU",
                "source": "mpstat",
                "breakouts": {
                    "num": [
                        "8",
                        "72"
                    ],
                    "thread": [
                        0,
                        1
                    ]
                }
            }
        """
        start = time.time()
        filters = self._build_metric_filters(run, metric, names, periods)
        metric_name = metric + ("" if not names else ("+" + ",".join(names)))
        metrics = await self.search(
            "metric_desc",
            filters=filters,
            ignore_unavailable=True,
        )
        if len(metrics["hits"]["hits"]) < 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Metric name {metric_name} not found for run {run}",
            )
        classes = set()
        response = {"label": metric}
        breakouts = defaultdict(list)
        pl = set()
        pidn = self._get_id_field("period")
        for m in self._hits(metrics):
            desc = m["metric_desc"]
            response["type"] = desc["type"]
            response["source"] = desc["source"]
            if desc.get("class"):
                classes.add(desc["class"])
            if "period" in m:
                pl.add(m["period"][pidn])
            for n, v in desc["names"].items():
                if v not in breakouts[n]:
                    breakouts[n].append(v)
        # We want to help filter a consistent summary, so only show those
        # names with more than one value.
        if len(pl) > 1:
            response["periods"] = sorted(pl)
        response["class"] = sorted(classes)
        response["breakouts"] = {n: v for n, v in breakouts.items() if len(v) > 1}
        self.logger.info("Processing took %.3f seconds", time.time() - start)
        return response

    async def get_metrics_data(
        self,
        run: str,
        metric: str,
        names: Optional[list[str]] = None,
        periods: Optional[list[str]] = None,
        aggregate: bool = False,
    ) -> list[Any]:
        """Return a list of metric data

        The "aggregate" option allows aggregating various metrics across
        breakout streams and periods: be careful, as this is meaningful only if
        the breakout streams are sufficiently related.

        Args:
            run: run ID
            metric: metric label (e.g., "mpstat::Busy-CPU")
            names: list of name filters ("cpu=3")
            periods: list of period IDs
            aggregate: aggregate multiple metric data streams

        Returns:
            A sequence of data samples, showing the aggregate sample along with
            the duration and end timestamp of each sample interval.

            [
                {
                    "begin": "2024-08-22 20:03:23.028000+00:00",
                    "end": "2024-08-22 20:03:37.127000+00:00",
                    "duration": 14.1,
                    "value": 9.35271216694379
                },
                {
                    "begin": "2024-08-22 20:03:37.128000+00:00",
                    "end": "2024-08-22 20:03:51.149000+00:00",
                    "duration": 14.022,
                    "value": 9.405932330557683
                },
                {
                    "begin": "2024-08-22 20:03:51.150000+00:00",
                    "end": "2024-08-22 20:04:05.071000+00:00",
                    "duration": 13.922,
                    "value": 9.478773265522682
                }
            ]
        """
        start = time.time()
        ids = await self._get_metric_ids(
            run, metric, names, periodlist=periods, aggregate=aggregate
        )

        # If we're searching by periods, filter metric data by the period
        # timestamp range rather than just relying on the metric desc IDs as
        # we also want to filter non-periodic tool data.
        mdidn = self._get_id_field("metric_desc")
        filters = [{"terms": {f"metric_desc.{mdidn}": ids}}]
        filters.extend(await self._build_timestamp_range_filters(periods))

        response = []

        # NOTE -- _get_metric_ids already failed if we found multiple IDs but
        # aggregation wasn't specified.
        if len(ids) > 1:
            # Find the minimum sample interval of the selected metrics
            aggdur = await self.search(
                "metric_data",
                size=0,
                filters=filters,
                aggregations={"duration": {"min": {"field": "metric_data.duration"}}},
            )
            if aggdur["aggregations"]["duration"].get("value", 0) > 0:
                interval = int(aggdur["aggregations"]["duration"]["value"])
                data = await self.search(
                    index="metric_data",
                    size=0,
                    filters=filters,
                    aggregations={
                        "interval": {
                            "histogram": {
                                "field": "metric_data.end",
                                "interval": interval,
                            },
                            "aggs": {"value": {"sum": {"field": "metric_data.value"}}},
                        }
                    },
                )
                for h in self._aggs(data, "interval"):
                    response.append(
                        {
                            "begin": self._format_timestamp(h["key"] - interval),
                            "end": self._format_timestamp(h["key"]),
                            "value": h["value"]["value"],
                            "duration": interval / 1000.0,
                        }
                    )
        else:
            data = await self.search("metric_data", filters=filters)
            for h in self._hits(data, ["metric_data"]):
                response.append(self._format_data(h))
        response.sort(key=lambda a: a["end"])
        self.logger.info("Processing took %.3f seconds", time.time() - start)
        return response

    async def get_metrics_summary(
        self, summaries: list[Metric]
    ) -> list[dict[str, Any]]:
        """Return a statistical summary of metric data

        Provides a statistical summary of selected data samples.

        Args:
            summaries: list of Summary objects to define desired metrics

        Returns:
            A statistical summary of the selected metric data
        """
        start = time.time()
        results = []
        params_by_run = {}
        periods_by_run = {}
        run_id_list = []
        mdidn = self._get_id_field("metric_desc")
        for s in summaries:
            if not s.run:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "each summary request must have a run ID",
                )
            if s.run not in run_id_list:
                run_id_list.append(s.run)
        for summary in summaries:
            ids = await self._get_metric_ids(
                summary.run,
                summary.metric,
                summary.names,
                periodlist=summary.periods,
                aggregate=summary.aggregate,
            )
            filters = [{"terms": {f"metric_desc.{mdidn}": ids}}]
            filters.extend(await self._build_timestamp_range_filters(summary.periods))
            data = await self.search(
                "metric_data",
                size=0,
                filters=filters,
                aggregations={
                    "score": {"extended_stats": {"field": "metric_data.value"}}
                },
            )

            # The caller can provide a title for each graph; but, if not, we
            # journey down dark overgrown pathways to fabricate a default with
            # reasonable context, including unique iteration parameters,
            # breakdown selections, and which run provided the data.
            if summary.title:
                title = summary.title
            else:
                title = await self._make_title(
                    summary.run, run_id_list, summary, params_by_run, periods_by_run
                )

            score = data["aggregations"]["score"]
            score["aggregate"] = summary.aggregate
            score["metric"] = summary.metric
            score["names"] = summary.names
            score["periods"] = summary.periods
            score["run"] = summary.run
            score["title"] = title
            results.append(score)
        duration = time.time() - start
        self.logger.info(f"Processing took {duration} seconds")
        return results

    async def get_metrics_graph(self, graphdata: GraphList) -> dict[str, Any]:
        """Return metrics data for a run

        Each run may have multiple performance metrics stored. This API allows
        retrieving graphable time-series representation of a metric over the
        period of the run, in the format defined by Plotly as configuration
        settings plus an x value array and a y value array.

        {
            "data": [
                {
                "x": [
                    "2024-08-27 09:16:27.371000",
                    ...
                ],
                "y": [
                    10.23444312132161,
                    ...
                ],
                "name": "Metric ilab::train-samples-sec",
                "type": "scatter",
                "mode": "line",
                "marker": {"color": "black"},
                "labels": {"x": "sample timestamp", "y": "samples / second"}
                }
            ]
            "layout": {
                "width": 1500,
                "yaxis": {
                    "title": "mpstat::Busy-CPU core=2,package=0,num=112,type=usr",
                    "color": "black"
                }
            }
        }

        Args:
            graphdata: A GraphList object

        Returns:
            A Plotly object with layout
        """
        start = time.time()
        graphlist = []
        if graphdata.relative:
            if graphdata.absolute_relative:
                x_label = "sample runtime (HH:MM:SS)"
                format = "%H:%M:%S"
            else:
                x_label = "sample runtime (seconds)"
                format = None
        else:
            x_label = "sample timestamp"
            format = "%Y:%M:%d %X %Z"
        xaxis = {
            "title": {
                "text": x_label,
                "font": {"color": "gray", "variant": "petite-caps", "weight": 1000},
            },
        }
        if format:
            xaxis["type"] = "date"
            xaxis["tickformat"] = format
        layout: dict[str, Any] = {
            "showlegend": True,
            "responsive": True,
            "autosize": True,
            "xaxis_title": x_label,
            "yaxis_title": "Metric value",
            "xaxis": xaxis,
            "legend": {
                "xref": "container",
                "yref": "container",
                "xanchor": "right",
                "yanchor": "top",
                "x": 0.9,
                "y": 1,
                "orientation": "h",
            },
        }
        axes = {}
        yaxis = None
        cindex = 0
        params_by_run = {}
        periods_by_run = {}

        # Construct a de-duped ordered list of run IDs, starting with the
        # default.
        run_id_list = []
        for g in graphdata.graphs:
            if not g.run:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "each graph request must have a run ID"
                )
            if g.run not in run_id_list:
                run_id_list.append(g.run)

        for g in graphdata.graphs:
            run_id = g.run
            names = g.names
            metric: str = g.metric
            run_idx = None
            if len(run_id_list) > 1:
                run_idx = f"Run {run_id_list.index(run_id) + 1}"

            # The caller can provide a title for each graph; but, if not, we
            # journey down dark overgrown pathways to fabricate a default with
            # reasonable context, including unique iteration parameters,
            # breakdown selections, and which run provided the data.
            if g.title:
                title = g.title
            else:
                title = await self._make_title(
                    run_id, run_id_list, g, params_by_run, periods_by_run
                )

            ids = await self._get_metric_ids(
                run_id,
                metric,
                names,
                periodlist=g.periods,
                aggregate=g.aggregate,
            )
            mdidn = self._get_id_field("metric_desc")
            filters = [{"terms": {f"metric_desc.{mdidn}": ids}}]
            filters.extend(await self._build_timestamp_range_filters(g.periods))
            y_max = 0.0
            points: list[Point] = []

            # If we're graphing multiple breakouts, e.g., total CPU across
            # modes or cores, we want to aggregate by timestamp interval.
            # Sample timestamps don't necessarily align, so the "histogram"
            # aggregation normalizes within the interval (based on the minimum
            # actual interval duration).
            if len(ids) > 1:
                # Find the minimum sample interval of the selected metrics
                aggdur = await self.search(
                    "metric_data",
                    size=0,
                    filters=filters,
                    aggregations={
                        "duration": {
                            "stats": {"field": "metric_data.duration"}
                        }
                    },
                )
                if aggdur["aggregations"]["duration"]["count"] > 0:
                    interval = int(aggdur["aggregations"]["duration"]["min"])
                    data = await self.search(
                        index="metric_data",
                        size=0,
                        filters=filters,
                        aggregations={
                            "interval": {
                                "histogram": {
                                    "field": "metric_data.begin",
                                    "interval": interval,
                                },
                                "aggs": {
                                    "value": {
                                        "sum": {"field": "metric_data.value"}
                                    }
                                },
                            }
                        },
                    )
                    for h in self._aggs(data, "interval"):
                        begin = int(h["key"])
                        end = begin + interval - 1
                        points.append(
                            Point(begin, end, float(h["value"]["value"]))
                        )
            else:
                data = await self.search("metric_data", filters=filters)
                for h in self._hits(data, ["metric_data"]):
                    points.append(
                        Point(int(h["begin"]), int(h["end"]), float(h["value"]))
                    )

            # Sort the graph points by timestamp so that Ploty will draw nice
            # lines. We graph both the "begin" and "end" timestamp of each
            # sample against the value to more clearly show the sampling
            # interval.
            x = []
            y = []

            first = None

            for p in sorted(points, key=lambda a: a.begin):
                if graphdata.relative:
                    if not first:
                        first = p.begin
                    if graphdata.absolute_relative:
                        s = self._format_timestamp(p.begin - first)
                        e = self._format_timestamp(p.end - first)
                    else:
                        s = (p.begin - first) / 1000
                        e = (p.end - first) / 1000
                    x.extend([s, e])
                else:
                    s = self._format_timestamp(p.begin)
                    e = self._format_timestamp(p.end)
                    x.extend([s, e])
                y.extend([p.value, p.value])
                y_max = max(y_max, p.value)

            if g.color:
                color = g.color
            else:
                color = COLOR_NAMES[cindex]
                cindex += 1
                if cindex >= len(COLOR_NAMES):
                    cindex = 0
            graphitem = {
                "x": x,
                "y": y,
                "name": title,
                "type": "scatter",
                "mode": "line",
                "marker": {"color": color},
            }

            if run_idx:
                graphitem["legendgroup"] = run_idx
                graphitem["legendgrouptitle"] = {
                    "text": run_idx,
                    "font": {"variant": "small-caps", "style": "italic"},
                }

            # Y-axis scaling and labeling is divided by benchmark label;
            # so store each we've created to reuse. (E.g., if we graph
            # 5 different mpstat::Busy-CPU periods, they'll share a single
            # Y axis.)
            if metric in axes:
                yref = axes[metric]
            else:
                if yaxis:
                    name = f"yaxis{yaxis}"
                    yref = f"y{yaxis}"
                    yaxis += 1
                    layout[name] = {
                        "title": metric,
                        "color": color,
                        "autorange": True,
                        "anchor": "free",
                        "autoshift": True,
                        "overlaying": "y",
                    }
                else:
                    name = "yaxis"
                    yref = "y"
                    yaxis = 2
                    layout[name] = {
                        "title": metric,
                        "color": color,
                    }
                axes[metric] = yref
            graphitem["yaxis"] = yref
            graphlist.append(graphitem)
        self.logger.info("Processing took %.3f seconds", time.time() - start)
        return {"data": graphlist, "layout": layout}
