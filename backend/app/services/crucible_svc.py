"""Service to pull data from a Crucible CDM OpenSearch data store

A set of helper methods to enable a project API to easily process data from a
Crucible controller's OpenSearch data backend.

This includes paginated, filtered, and sorted lists of benchmark runs, along
access to the associated Crucible documents such as iterations, samples, and
periods. Metric data can be accessed by breakout names, or aggregated by
breakout subsets or collection periods as either raw data points, statistical
aggregate, or Plotly graph format for UI display.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator, Optional, Tuple, Union

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import HTTPException, status
from pydantic import BaseModel

from app import config


class Graph(BaseModel):
    """Describe a single graph

    This represents a JSON object provided by a caller through the get_graph
    API to describe a specific metric graph.

    The default title (if the field is omitted) is the metric label with a
    suffix denoting breakout values selected, any unique parameter values
    in a selected iteration, and (if multiple runs are selected in any Graph
    list) an indication of the run index. For example,
    "mpstat::Busy-CPU [core=2,type=usr] (batch-size=16)".

    Fields:
        metric: the metric label, "ilab::train-samples-sec"
        aggregate: True to aggregate unspecified breakouts
        color: CSS color string ("green" or "#008000")
        names: Lock in breakouts
        periods: Select metrics for specific test period(s)
        run: Override the default run ID from GraphList
        title: Provide a title for the graph. The default is a generated title
    """

    metric: str
    aggregate: bool = False
    color: Optional[str] = None
    names: Optional[list[str]] = None
    periods: Optional[list[str]] = None
    run: Optional[str] = None
    title: Optional[str] = None


class GraphList(BaseModel):
    """Describe a set of overlaid graphs

    This represents a JSON object provided by a caller through the get_graph
    API to introduce a set of constrained metrics to be graphed. The "run
    ID" here provides a default for the embedded Graph objects, and can be
    omitted if all Graph objects specify a run ID. (This is most useful to
    select a set of graphs all for a single run ID.)

    Fields:
        run: Specify the (default) run ID
        name: Specify a name for the set of graphs
        graphs: a list of Graph objects
    """

    run: Optional[str] = None
    name: str
    graphs: list[Graph]


@dataclass
class Point:
    """Graph point

    Record the start & end timestamp and value of a metric data point
    """

    begin: int
    end: int
    value: float


colors = [
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

    def __init__(self, configpath: str = "crucible"):
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
        self.elastic = AsyncElasticsearch(self.url, basic_auth=self.auth)

    @staticmethod
    def _get_index(root: str) -> str:
        return "cdmv7dev-" + root

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
            elif isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    pass
                try:
                    d = datetime.fromisoformat(value)
                    return int(d.timestamp() * 1000.0)
                except ValueError:
                    pass
        except Exception as e:
            print(f"normalizing {type(value).__name__} {value} failed with {str(e)}")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Date representation {value} is not a date string or timestamp",
            )

    @staticmethod
    def _hits(
        payload: dict[str, Any], fields: Optional[list[str]] = None
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
        if "hits" not in payload:
            raise HTTPException(
                status_code=500, detail=f"Attempt to iterate hits for {payload}"
            )
        hits = payload.get("hits", {}).get("hits", [])
        for h in hits:
            source = h["_source"]
            if fields:
                for f in fields:
                    source = source[f]
            yield source

    @staticmethod
    def _aggs(payload: dict[str, Any], aggregation: str) -> Iterator[dict[str, Any]]:
        """Helper to access OpenSearch aggregations

        Iteratively yields the name and value of each aggregation returned
        by an OpenSearch query. This can also be used for nested aggregations
        by specifying an aggregation object.

        Args:
            payload: A JSON dict containing an "aggregations" field

        Returns:
            Yields each aggregation from an aggregation bucket list
        """
        if "aggregations" not in payload:
            raise HTTPException(
                status_code=500,
                detail=f"Attempt to iterate missing aggregations for {payload}",
            )
        aggs = payload["aggregations"]
        if aggregation not in aggs:
            raise HTTPException(
                status_code=500,
                detail=f"Attempt to iterate missing aggregation {aggregation} for {payload}",
            )
        for agg in aggs[aggregation]["buckets"]:
            yield agg

    @staticmethod
    def _format_timestamp(timestamp: Union[str, int]) -> str:
        """Convert stringified integer milliseconds-from-epoch to ISO date"""
        try:
            ts = int(timestamp)
        except Exception as e:
            print(f"ERROR: invalid {timestamp!r}: {str(e)!r}")
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

    @classmethod
    def _format_period(cls, period: dict[str, Any]) -> dict[str, Any]:
        """Helper to format a "period" object

        Crucible stores the date values as stringified integers, so this
        converts the begin and end timestamps to ISO date-time strings.

        Args:
            period: a "period" object

        Returns:
            A neatly formatted "period" object
        """
        return {
            "begin": cls._format_timestamp(timestamp=period["begin"]),
            "end": cls._format_timestamp(period["end"]),
            "id": period["id"],
            "name": period["name"],
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
                    status.HTTP_400_BAD_REQUEST, f"Filter item {e} must be '<k>=<v>'"
                )
            filters.append({"term": {f"metric_desc.names.{n}": v}})
        return filters

    @classmethod
    def _build_period_filters(
        cls, periodlist: Optional[list[str]] = None
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
        pl: list[str] = cls._split_list(periodlist)
        if pl:
            return [
                {
                    "dis_max": {
                        "queries": [
                            {"bool": {"must_not": {"exists": {"field": "period"}}}},
                            {"terms": {"period.id": pl}},
                        ]
                    }
                }
            ]
        else:
            return []

    @classmethod
    def _build_metric_filters(
        cls,
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
        return (
            [
                {"term": {"run.id": run}},
                {"term": {"metric_desc.source": msource}},
                {"term": {"metric_desc.type": mtype}},
            ]
            + cls._build_name_filters(names)
            + cls._build_period_filters(periods)
        )

    @classmethod
    def _build_sort_terms(cls, sorters: Optional[list[str]]) -> list[dict[str, str]]:
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
                        f"Sort direction {dir!r} must be one of {','.join(DIRECTIONS)}",
                    )
                if key not in cls.FIELDS:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Sort key {key!r} must be one of {','.join(FIELDS)}",
                    )
                sort_terms.append({f"run.{key}": dir})
        else:
            sort_terms = [{"run.begin": "asc"}]
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
        print(
            f"QUERY on {idx} took {time.time() - start} seconds, "
            f"hits: {value.get('hits', {}).get('total')}"
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
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                (
                    f"No matches for {metric}"
                    f"{('+' + ','.join(namelist) if namelist else '')}"
                ),
            )
        ids = [h["metric_desc"]["id"] for h in self._hits(metrics)]
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
        for m in self._hits(metrics):
            if "period" in m:
                periods.add(m["period"]["id"])
            for n, v in m["metric_desc"]["names"].items():
                names[n].add(v)

        # We want to help filter a consistent summary, so only show those
        # breakout names with more than one value.
        response["names"] = {n: sorted(v) for n, v in names.items() if v and len(v) > 1}
        response["periods"] = list(periods)
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
            matches = await self.search(
                "period", filters=[{"terms": {"period.id": ps}}]
            )
            start = None
            end = None
            for h in self._hits(matches):
                p = h["period"]
                st = p["begin"]
                et = p["end"]

                # If any period is missing a timestamp, use the run's timestamp
                # instead to avoid blowing up on a CDM error.
                if st is None:
                    st = h["run"]["begin"]
                if et is None:
                    et = h["run"]["end"]
                if st and (not start or st < start):
                    start = st
                if et and (not end or et > end):
                    end = et
            if start is None or end is None:
                name = (
                    f"{h['run']['benchmark']}:{h['run']['begin']}-"
                    f"{h['iteration']['num']}-{h['sample']['num']}-"
                    f"{p['name']}"
                )
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Unable to compute {name!r} time range {start!r} -> {end!r}",
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

        Documents in the specified index must have "run.id" fields. Returns
        a set of unique run IDs matched by the filter in the specified index.

        Args:
            index: root CDM index name
            filters: a list of OpenSearch filter terms

        Returns:
            a set of unique run ID values
        """
        filtered = await self.search(
            index, source="run.id", filters=filters, ignore_unavailable=True
        )
        print(f"HITS: {filtered['hits']['hits']}")
        return set([x for x in self._hits(filtered, ["run", "id"])])

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
            s = None
            e = None
            if start:
                s = self._normalize_date(start)
                results["startDate"] = datetime.fromtimestamp(
                    s / 1000.0, tz=timezone.utc
                )
            if end:
                e = self._normalize_date(end)
                results["endDate"] = datetime.fromtimestamp(e / 1000.0, tz=timezone.utc)

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

        iterations = defaultdict(list)
        tags = defaultdict(defaultdict)
        params = defaultdict(defaultdict)
        run_params = defaultdict(list)

        for i in self._hits(rawiterations):
            iterations[i["run"]["id"]].append(i["iteration"])

        # Organize tags by run ID
        for t in self._hits(rawtags):
            tags[t["run"]["id"]][t["tag"]["name"]] = t["tag"]["val"]

        # Organize params by iteration ID
        for p in self._hits(rawparams):
            run_params[p["run"]["id"]].append(p)
            params[p["iteration"]["id"]][p["param"]["arg"]] = p["param"]["val"]

        runs = {}
        for h in self._hits(hits):
            run = h["run"]
            rid = run["id"]

            # Filter the runs by our tag and param queries
            if param_filters and rid not in paramids:
                continue

            if tag_filters and rid not in tagids:
                continue

            # Collect unique runs: the status is "fail" if any iteration for
            # that run ID failed.
            runs[rid] = run
            run["tags"] = tags.get(rid, {})
            run["iterations"] = []
            run["primary_metrics"] = set()
            common = CommonParams()
            for i in iterations.get(rid, []):
                iparams = params.get(i["id"], {})
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
            run["params"] = common.render()
            try:
                run["begin_date"] = self._format_timestamp(run["begin"])
                run["end_date"] = self._format_timestamp(run["end"])
            except KeyError as e:
                print(f"Missing 'run' key {str(e)} in {run}")
                run["begin_date"] = self._format_timestamp("0")
                run["end_date"] = self._format_timestamp("0")

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
        tags = await self.search(
            index="tag",
            filters=[{"term": {"run.id": run}}],
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
        match = {"run.id" if run else "iteration.id": run if run else iteration}
        params = await self.search(
            index="param",
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        response = defaultdict(defaultdict)
        for param in self._hits(params):
            iter = param["iteration"]["id"]
            arg = param["param"]["arg"]
            val = param["param"]["val"]
            if response.get(iter) and response.get(iter).get(arg):
                print(f"Duplicate param {arg} for iteration {iter}")
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
        iterations = await self.search(
            index="iteration",
            filters=[{"term": {"run.id": run}}],
            sort=[{"iteration.num": "asc"}],
            **kwargs,
            ignore_unavailable=True,
        )
        return [i["iteration"] for i in self._hits(iterations)]

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
        match = {"run.id" if run else "iteration.id": run if run else iteration}
        hits = await self.search(
            index="sample",
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        samples = []
        for s in self._hits(hits):
            print(f"SAMPLE's ITERATION {s['iteration']}")
            sample = s["sample"]
            sample["iteration"] = s["iteration"]["num"]
            sample["primary_metric"] = s["iteration"]["primary-metric"]
            sample["status"] = s["iteration"]["status"]
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
        if sample:
            match = {"sample.id": sample}
        elif iteration:
            match = {"iteration.id": iteration}
        else:
            match = {"run.id": run}
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
            period["primary_metric"] = h["iteration"]["primary-metric"]
            period["status"] = h["iteration"]["status"]
            body.append(period)
        return body

    async def get_timeline(self, run: str, **kwargs) -> dict[str, Any]:
        """Report the relative timeline of a run

        With nested object lists, show runs to iterations to samples to
        periods.

        Args:
            run: run ID
            kwargs: additional OpenSearch parameters
        """
        itr = await self.search(
            index="iteration",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        sam = await self.search(
            index="sample",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        per = await self.search(
            index="period",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        samples = defaultdict(list)
        periods = defaultdict(list)

        for s in self._hits(sam):
            samples[s["iteration"]["id"]].append(s)
        for p in self._hits(per):
            periods[p["sample"]["id"]].append(p)

        iterations = []
        robj = {"id": run, "iterations": iterations}
        body = {"run": robj}
        for i in self._hits(itr):
            if "begin" not in robj:
                robj["begin"] = self._format_timestamp(i["run"]["begin"])
                robj["end"] = self._format_timestamp(i["run"]["end"])
            iteration = i["iteration"]
            iterations.append(iteration)
            iteration["samples"] = []
            for s in samples.get(iteration["id"], []):
                sample = s["sample"]
                sample["periods"] = []
                for pr in periods.get(sample["id"], []):
                    period = self._format_period(pr["period"])
                    sample["periods"].append(period)
                iteration["samples"].append(sample)
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
        hits = await self.search(
            index="metric_desc",
            filters=[{"term": {"run.id": run}}],
            ignore_unavailable=True,
            **kwargs,
        )
        met = {}
        for h in self._hits(hits):
            desc = h["metric_desc"]
            name = desc["source"] + "::" + desc["type"]
            if name in met:
                record = met[name]
            else:
                record = {"periods": [], "breakouts": defaultdict(set)}
                met[name] = record
            if "period" in h:
                record["periods"].append(h["period"]["id"])
            for n, v in desc["names"].items():
                record["breakouts"][n].add(v)
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
        response = {"label": metric, "class": classes}
        breakouts = defaultdict(set)
        pl = set()
        for m in self._hits(metrics):
            desc = m["metric_desc"]
            response["type"] = desc["type"]
            response["source"] = desc["source"]
            if desc.get("class"):
                classes.add(desc["class"])
            if "period" in m:
                pl.add(m["period"]["id"])
            for n, v in desc["names"].items():
                breakouts[n].add(v)
        # We want to help filter a consistent summary, so only show those
        # names with more than one value.
        if len(pl) > 1:
            response["periods"] = pl
        response["breakouts"] = {n: v for n, v in breakouts.items() if len(v) > 1}
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
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
        filters = [{"terms": {"metric_desc.id": ids}}]
        filters.extend(await self._build_timestamp_range_filters(periods))

        response = []
        if len(ids) > 1:
            # Find the minimum sample interval of the selected metrics
            aggdur = await self.search(
                "metric_data",
                size=0,
                filters=filters,
                aggregations={"duration": {"stats": {"field": "metric_data.duration"}}},
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
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
        return response

    async def get_metrics_summary(
        self,
        run: str,
        metric: str,
        names: Optional[list[str]] = None,
        periods: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Return a statistical summary of metric data

        Provides a statistical summary of selected data samples.

        Args:
            run: run ID
            metric: metric label (e.g., "mpstat::Busy-CPU")
            names: list of name filters ("cpu=3")
            periods: list of period IDs

        Returns:
            A statistical summary of the selected metric data

            {
                "count": 71,
                "min": 0.0,
                "max": 0.3296,
                "avg": 0.02360704225352113,
                "sum": 1.676self.BIGQUERY00000001
            }
        """
        start = time.time()
        ids = await self._get_metric_ids(run, metric, names, periodlist=periods)
        filters = [{"terms": {"metric_desc.id": ids}}]
        filters.extend(await self._build_timestamp_range_filters(periods))
        data = await self.search(
            "metric_data",
            size=0,
            filters=filters,
            aggregations={"score": {"stats": {"field": "metric_data.value"}}},
        )
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
        return data["aggregations"]["score"]

    async def _graph_title(
        self,
        run_id: str,
        run_id_list: list[str],
        graph: Graph,
        params_by_run: dict[str, Any],
        periods_by_run: dict[str, Any],
    ) -> str:
        """Compute a default title for a graph

        Use the period, breakout name selections, run list, and iteration
        parameters to construct a meaningful name for a graph.

        For example, "ilab::sdg-samples-sec (batch-size=4) {run 1}", or
        "mpstat::Busy-CPU [cpu=4]"

        Args:
            run_id: the Crucible run ID
            run_id_list: ordered list of run IDs in our list of graphs
            graph: the current Graph object
            params_by_run: initially empty dict used to cache parameters
            periods_by_run: initially empty dict used to cache periods

        Returns:
            A string title
        """
        names = graph.names
        metric = graph.metric
        if run_id not in params_by_run:
            # Gather iteration parameters outside the loop for help in
            # generating useful labels.
            all_params = await self.search(
                "param", filters=[{"term": {"run.id": run_id}}]
            )
            collector = defaultdict(defaultdict)
            for h in self._hits(all_params):
                collector[h["iteration"]["id"]][h["param"]["arg"]] = h["param"]["val"]
            params_by_run[run_id] = collector
        else:
            collector = params_by_run[run_id]

        if run_id not in periods_by_run:
            periods = await self.search(
                "period", filters=[{"term": {"run.id": run_id}}]
            )
            iteration_periods = defaultdict(set)
            for p in self._hits(periods):
                iteration_periods[p["iteration"]["id"]].add(p["period"]["id"])
            periods_by_run[run_id] = iteration_periods
        else:
            iteration_periods = periods_by_run[run_id]

        # We can easily end up with multiple graphs across distinct
        # periods or iterations, so we want to be able to provide some
        # labeling to the graphs. We do this by looking for unique
        # iteration parameters values, since the iteration number and
        # period name aren't useful by themselves.
        name_suffix = ""
        if graph.periods:
            iteration = None
            for i, pset in iteration_periods.items():
                if set(graph.periods) <= pset:
                    iteration = i
                    break

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
                    name_suffix = (
                        " (" + ",".join([f"{p}={v}" for p, v in unique.items()]) + ")"
                    )

        if len(run_id_list) > 1:
            name_suffix += f" {{run {run_id_list.index(run_id) + 1}}}"

        options = (" [" + ",".join(names) + "]") if names else ""
        return metric + options + name_suffix

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
        default_run_id = graphdata.run
        layout: dict[str, Any] = {"width": "1500"}
        axes = {}
        yaxis = None
        cindex = 0
        params_by_run = {}
        periods_by_run = {}

        # Construct a de-duped ordered list of run IDs, starting with the
        # default.
        run_id_list = []
        if default_run_id:
            run_id_list.append(default_run_id)
        run_id_missing = False
        for g in graphdata.graphs:
            if g.run:
                if g.run not in run_id_list:
                    run_id_list.append(g.run)
            else:
                run_id_missing = True

        if run_id_missing and not default_run_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "each graph request must have a run ID"
            )

        for g in graphdata.graphs:
            run_id = g.run if g.run else default_run_id
            names = g.names
            metric: str = g.metric

            # The caller can provide a title for each graph; but, if not, we
            # journey down dark overgrown pathways to fabricate a default with
            # reasonable context, including unique iteration parameters,
            # breakdown selections, and which run provided the data.
            if g.title:
                title = g.title
            else:
                title = await self._graph_title(
                    run_id, run_id_list, g, params_by_run, periods_by_run
                )

            ids = await self._get_metric_ids(
                run_id,
                metric,
                names,
                periodlist=g.periods,
                aggregate=g.aggregate,
            )
            filters = [{"terms": {"metric_desc.id": ids}}]
            filters.extend(await self._build_timestamp_range_filters(g.periods))
            y_max = 0.0
            points: list[Point] = []

            # If we're pulling multiple breakouts, e.g., total CPU across modes
            # or cores, we want to aggregate by timestamp interval. Sample
            # timstamps don't necessarily align, so the "histogram" aggregation
            # normalizes within the interval (based on the minimum actual
            # interval duration).
            if len(ids) > 1:
                # Find the minimum sample interval of the selected metrics
                aggdur = await self.search(
                    "metric_data",
                    size=0,
                    filters=filters,
                    aggregations={
                        "duration": {"stats": {"field": "metric_data.duration"}}
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
                                    "value": {"sum": {"field": "metric_data.value"}}
                                },
                            }
                        },
                    )
                    for h in self._aggs(data, "interval"):
                        begin = int(h["key"])
                        end = begin + interval - 1
                        points.append(Point(begin, end, float(h["value"]["value"])))
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

            for p in sorted(points, key=lambda a: a.begin):
                x.extend(
                    [self._format_timestamp(p.begin), self._format_timestamp(p.end)]
                )
                y.extend([p.value, p.value])
                y_max = max(y_max, p.value)

            if g.color:
                color = g.color
            else:
                color = colors[cindex]
                cindex += 1
                if cindex >= len(colors):
                    cindex = 0
            graphitem = {
                "x": x,
                "y": y,
                "name": title,
                "type": "scatter",
                "mode": "line",
                "marker": {"color": color},
                "labels": {
                    "x": "sample timestamp",
                    "y": "samples / second",
                },
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
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
        return {"data": graphlist, "layout": layout}
