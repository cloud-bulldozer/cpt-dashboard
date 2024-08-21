from dataclasses import dataclass
import sys
from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Any, Iterator, Optional, Tuple, Union

from pydantic import BaseModel

from app import config
from elasticsearch import Elasticsearch, NotFoundError
from fastapi import HTTPException, status


class Graph(BaseModel):
    metric: str
    aggregate: bool = False
    names: Optional[list[str]] = None
    periods: Optional[list[str]] = None


class GraphList(BaseModel):
    run: str
    name: str
    graphs: list[Graph]


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


class CrucibleService:

    def __init__(self, configpath="crucible"):
        """Initialize a Crucible CDM (OpenSearch) connection.

        This includes making an "info" call to confirm and record the server
        response.

        Args:
            configpath: The Vyper config path (e.g., "ilab.crucible")
        """
        self.cfg = config.get_config()
        self.user = self.cfg.get(configpath + ".username")
        self.password = self.cfg.get(configpath + ".password")
        self.auth = (self.user, self.password) if self.user or self.password else None
        self.url = self.cfg.get(configpath + ".url")
        self.elastic = Elasticsearch(self.url, basic_auth=self.auth)
        self.info = None
        try:
            self.info = self.elastic.info()  # Test the connection
        except Exception as e:
            print(f"Failed to connect: {e}", file=sys.stderr)
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                f"The configured Crucible search instance ({self.url}) does not respond",
            )

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
    def normalize_date(value: Optional[Union[int, str, datetime]]) -> int:
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
        optional "fields" as ["metric_desc"] will yield the equivalent of
        hit["_source"]["metric_desc"]

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
            Yields each aggregation from an aggregations object
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
    def _date(timestamp: str) -> str:
        """Convert stringified integer milliseconds-from-epoch to ISO date"""
        return str(datetime.fromtimestamp(int(timestamp) / 1000, timezone.utc))

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
            "begin": cls._date(data["begin"]),
            "end": cls._date(data["end"]),
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
            "begin": cls._date(timestamp=period["begin"]),
            "end": cls._date(period["end"]),
            "id": period["id"],
            "name": period["name"],
        }

    @classmethod
    def _build_filter_options(
        cls, filter: Optional[list[str]] = None
    ) -> Tuple[Optional[list[dict[str, Any]]], Optional[list[dict[str, Any]]]]:
        """Build filter terms for tag and parameter filter terms

        Args:
            filter: list of filter terms like "param:key=value"

        Returns:
            An OpenSearch filter list to apply the filters
        """
        terms = defaultdict(list)
        for term in cls._split_list(filter):
            p = Parser(term)
            namespace, _ = p._next_token([":"])
            key, operation = p._next_token(["="])
            value, _ = p._next_token()
            print(f"FILTER: {namespace}:{key}{operation}{value}")
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
                            {"term": {value_field: value}},
                        ]
                    }
                }
            )
        param_filter = None
        tag_filter = None
        if "param" in terms:
            param_filter = [{"dis_max": {"queries": terms["param"]}}]
        if "tag" in terms:
            tag_filter = [{"dis_max": {"queries": terms["tag"]}}]
        return param_filter, tag_filter

    @classmethod
    def _name_filters(
        cls, namelist: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Build filter terms for metric breakdown names

        for example, "cpu=10" filters for metric data descriptors where the
        breakdown name "cpu" exists and has a value of 10.

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
    def _period_filters(
        cls, periodlist: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Build period filters

        Generate filter terms to match against a list of period IDs.

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
    def _filter_metric_desc(
        cls,
        run: str,
        metric: str,
        names: Optional[list[str]] = None,
        periods: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Helper for filtering metric descriptions

        We normally filter by run, metric "label", and optionally by breakout
        names and periods. This encapsulates the filter contruction.

        Args:
            run: run ID
            metric: metric label (ilab::sdg-samples-sec)
            names: list of "name=value" filters
            periods: list of period IDs

        Returns:
            A list of OpenSearch filter expressions
        """
        source, type = metric.split("::")
        return (
            [
                {"term": {"run.id": run}},
                {"term": {"metric_desc.source": source}},
                {"term": {"metric_desc.type": type}},
            ]
            + cls._name_filters(names)
            + cls._period_filters(periods)
        )

    @staticmethod
    def _get_index(root: str) -> str:
        return "cdmv7dev-" + root

    def _search(
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
        value = self.elastic.search(index=idx, body=query, **kwargs)
        print(
            f"QUERY on {idx} took {time.time() - start} seconds, "
            f"hits: {value.get('hits', {}).get('total')}"
        )
        return value

    def search(
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
            "size": 250000 if size is None else size,
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
        return self._search(index, query, **kwargs)

    def _get_metric_ids(
        self,
        run: str,
        metric: str,
        namelist: Optional[list[str]] = None,
        periodlist: Optional[list[str]] = None,
        highlander: bool = True,
    ) -> list[str]:
        """Generate a list of matching metric_desc IDs

        Given a specific run and metric name, and a set of breakout filters,
        returns a list of metric desc IDs that match.

        Generally, breakout data isn't useful unless the set of filters
        produces a single metric desc ID, however this can be overridden.

        If a single ID is required to produce a consistent metric, and the
        supplied filters produce more than one, raise a 422 HTTP error
        (UNPROCESSABLE CONTENT) with a response body showing the unsatisfied
        breakouts (name and available values).

        Args:
            run: run ID
            metric: combined metric name (e.g., sar-net::packets-sec)
            namelist: a list of breakout filters like "type=physical"
            periodlist: a list of period IDs
            highlander: if True, there can be only one (metric ID)

        Returns:
            A list of matching metric_desc ID value(s)
        """
        filters = self._filter_metric_desc(run, metric, namelist, periodlist)
        metrics = self.search(
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
        if len(ids) < 2 or not highlander:
            return ids

        # This probably means we're not filtering well enouch for a useful
        # summary. Diagnose how to improve it.
        names = defaultdict(set)
        periods = set()
        response = {
            "message": f"More than one metric ({len(ids)}) probably means "
            "you should add filters"
        }
        for m in self._hits(metrics):
            if "period" in m:
                periods.add(m["period"]["id"])
            for n, v in m["metric_desc"]["names"].items():
                names[n].add(v)

        # We want to help filter a consistent summary, so only show those
        # names with more than one value.
        response["names"] = {n: sorted(v) for n, v in names.items() if len(v) > 1}
        response["periods"] = list(periods)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=[response]
        )

    def _data_range(self, periods: Optional[list[str]] = None) -> list[dict[str, Any]]:
        """Create a timestamp range filter

        Args:
            periods: a list of CDM period IDs

        Returns:
            Constructs a range filter for the earliest begin timestamp and the
            latest end timestamp among the specified periods.
        """
        if periods:
            ps = self._split_list(periods)
            matches = self.search("period", filters=[{"terms": {"period.id": ps}}])
            start = min([int(h["begin"]) for h in self._hits(matches, ["period"])])
            end = max([int(h["end"]) for h in self._hits(matches, ["period"])])
            return [
                {"range": {"metric_data.begin": {"gte": str(start)}}},
                {"range": {"metric_data.end": {"lte": str(end)}}},
            ]
        else:
            return []

    def _get_run_ids(
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
        filtered = self.search(
            index, source="run.id", filters=filters, ignore_unavailable=True
        )
        return set([x["id"] for x in self._hits(filtered, ["run"])])

    def run_filters(self) -> dict[str, dict[str, int]]:
        """Return possible tag and filter terms

        Return a description of tag and param filter terms meaningful
        across all datasets. TODO: we should support date-range and benchmark
        filtering. Consider supporting all `run` API filtering, which would
        allow adjusting the filter popups to drop options no longer relevant
        to a given set.

        Returns:
            A three-level JSON dict; the first level is the namespace (param or
            tag), the second level is the parameter or tag name, the third
            level key is each value present in the index, and the value is the
            number of times that value appears.

            {
                "param": {
                    {"gpus": {
                        "4": 22,
                        "8": 2
                    }
                }
            }
        """
        tags = self.search(
            "tag",
            size=0,
            aggregations={
                "key": {
                    "terms": {"field": "tag.name", "size": 10000},
                    "aggs": {"values": {"terms": {"field": "tag.val", "size": 10000}}},
                }
            },
            ignore_unavailable=True,
        )
        params = self.search(
            "param",
            size=0,
            aggregations={
                "key": {
                    "terms": {"field": "param.arg", "size": 10000},
                    "aggs": {
                        "values": {"terms": {"field": "param.val", "size": 10000}}
                    },
                }
            },
            ignore_unavailable=True,
        )
        result = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for t in self._aggs(params, "key"):
            for v in t["values"]["buckets"]:
                result["param"][t["key"]][v["key"]] += v["doc_count"]
        for t in self._aggs(tags, "key"):
            for v in t["values"]["buckets"]:
                result["tag"][t["key"]][v["key"]] += v["doc_count"]
        return result

    def runs(
        self,
        benchmark: Optional[str] = None,
        filter: Optional[list[str]] = None,
        name: Optional[str] = None,
        start: Optional[Union[int, str, datetime]] = None,
        end: Optional[Union[int, str, datetime]] = None,
        offset: Optional[int] = None,
        sort: Optional[list[str]] = None,
        size: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Return matching Crucible runs

        Filtered list of runs

        Args:
            benchmark: Include runs with specified benchmark name
            name: Include runs by owner name
            start: Include runs starting at timestamp
            end: Include runs ending no later than timestamp
            filter: List of tag/param filter terms (parm:key=value)
            sort: List of sort terms (column:<dir>)
            size: Include up to <size> runs in output
            offset: Use size/from pagination instead of search_after

        Returns:
            JSON object with "runs" list, "size", "next", and "total" fields.
        """

        # We need to remove runs which don't match against 'tag' or 'param'
        # filter terms. The CDM schema doesn't make it possible to do this in
        # one shot. Instead, we run queries against the param and tag indices
        # separately, producing a list of run IDs which we'll exclude from the
        # final collection.
        #
        # If there are no matches, we can exit early. (TODO: should this be an
        # error, or just a success with an empty list?)
        param_filters, tag_filters = self._build_filter_options(filter)
        results = {}
        filters = []
        if benchmark:
            filters.append({"term": {"run.benchmark": benchmark}})
        if name:
            filters.append({"term": {"run.name": name}})
        if start or end:
            s = None
            e = None
            if start:
                s = self.normalize_date(start)
                results["startDate"] = datetime.fromtimestamp(
                    s / 1000.0, tz=timezone.utc
                )
            if end:
                e = self.normalize_date(end)
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
        if sort:
            sorters = self._split_list(sort)
            results["sort"] = sorters
            sort_terms = []
            for s in sorters:
                DIRECTIONS = ("asc", "desc")
                FIELDS = (
                    "begin",
                    "benchmark",
                    "email",
                    "end",
                    "id",
                    "name",
                    "source",
                    "status",
                )
                key, dir = s.split(":", maxsplit=1)
                if dir not in DIRECTIONS:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Sort direction {dir!r} must be one of {','.join(DIRECTIONS)}",
                    )
                if key not in FIELDS:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Sort key {key!r} must be one of {','.join(FIELDS)}",
                    )
                sort_terms.append({f"run.{key}": dir})
        else:
            sort_terms = [{"run.begin": "asc"}]

        if size:
            results["size"] = size
        if offset:
            results["offset"] = offset

        # In order to filter by param or tag values, we need to produce a list
        # of matching RUN IDs from each index. We'll then drop any RUN ID that's
        # not on both lists.
        if tag_filters:
            tagids = self._get_run_ids("tag", tag_filters)
        if param_filters:
            paramids = self._get_run_ids("param", param_filters)

        # If it's obvious we can't produce any matches at this point, exit.
        if (tag_filters and len(tagids) == 0) or (param_filters and len(paramids) == 0):
            results.update({"results": [], "count": 0, "total": 0})
            return results

        hits = self.search(
            "iteration",
            size=size,
            offset=offset,
            sort=sort_terms,
            filters=filters,
            **kwargs,
            ignore_unavailable=True,
        )
        rawtags = self.search("tag", ignore_unavailable=True)
        rawparams = self.search("param", ignore_unavailable=True)

        tags = defaultdict(defaultdict)
        params = defaultdict(defaultdict)
        run_params = defaultdict(list)

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
            iteration = h["iteration"]
            iid = iteration["id"]
            rid = run["id"]
            iparams = params.get(iid, {})

            # Filter the runs by our tag and param queries
            if param_filters and rid not in paramids:
                continue

            if tag_filters and rid not in tagids:
                continue

            # Collect unique runs: the status is "fail" if any iteration for
            # that run ID failed.
            if rid not in runs:
                runs[rid] = run
                run["status"] = iteration["status"]
                try:
                    run["begin_date"] = self._date(run["begin"])
                    run["end_date"] = self._date(run["end"])
                except KeyError as e:
                    print(f"Missing 'run' key {str(e)} in {run}")
                    run["begin_date"] = self._date("0")
                    run["end_date"] = self._date("0")
                run["params"] = iparams.copy()
                run["iterations"] = [
                    {
                        "iteration": iteration["num"],
                        "primary_metric": iteration["primary-metric"],
                        "primary_period": iteration["primary-period"],
                        "status": iteration["status"],
                        "params": iparams,
                    }
                ]
                run["primary_metrics"] = set([iteration["primary-metric"]])
                run["tags"] = tags.get(rid, {})
            else:
                r = runs[rid]
                r["iterations"].append(
                    {
                        "iteration": iteration["num"],
                        "metric": iteration["primary-metric"],
                        "status": iteration["status"],
                        "params": iparams,
                    }
                )

                # Iteration-specific parameter names or values are factored out
                # of the run summary. (NOTE: listify the keys first so Python
                # doesn't complain about deletion during the traversal.)
                p = r["params"]
                for k in list(p.keys()):
                    if k not in iparams or p[k] != iparams[k]:
                        del p[k]
                r["primary_metrics"].add(iteration["primary-metric"])
                if iteration["status"] != "pass":
                    r["status"] = iteration["status"]
        results.update(
            {
                "results": list(runs.values()),
                "count": len(runs),
                "total": hits["hits"]["total"]["value"],
            }
        )
        if offset:
            results["next_offset"] = offset + size if size else len(runs)
        return results

    def tags(self, run: str, **kwargs) -> dict[str, str]:
        """Return the set of tags associated with a run

        Args:
            run: run ID

        Returns:
            JSON dict with "tag" keys showing each value
        """
        tags = self.search(
            index="tag",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        return {t["name"]: t["val"] for t in self._hits(tags, ["tag"])}

    def params(
        self, run: Optional[str] = None, iteration: Optional[str] = None, **kwargs
    ) -> dict[str, dict[str, str]]:
        """Return the set of parameters for a run or iteration

        Parameters are technically associated with an iteration, but can be
        aggregated for a run. (Note that, technically, values might vary across
        iterations, and only one will be returned. This is OK if a run has a
        single iteration, or if you know they're consistent.)

        Args:
            run: run ID
            iteration: iteration ID
            kwargs: additional OpenSearch keywords

        Returns:
            JSON dict of param key: value
        """
        if not run and not iteration:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "A params query requires either a run or iteration ID",
            )
        match = {"run.id" if run else "iteration.id": run if run else iteration}
        params = self.search(
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
            common = {}
            for iter, params in response.items():
                if not common:
                    common = dict(params)
                else:
                    # We can't change a dict during iteration, so iterate over
                    # a list of the param keys.
                    for param in list(common.keys()):
                        if param not in params or params[param] != common[param]:
                            del common[param]
            response["common"] = common
        return response

    def iterations(self, run: str, **kwargs) -> list[dict[str, Any]]:
        """Return a list of iterations for a run

        Args:
            run: run ID
            kwargs: additional OpenSearch keywords

        Returns:
            A list of iteration documents
        """
        iterations = self.search(
            index="iteration",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        return [i["iteration"] for i in self._hits(iterations)]

    def samples(
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
        samples = self.search(
            index="sample",
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        return [i["sample"] for i in self._hits(samples)]

    def periods(
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
        periods = self.search(
            index="period",
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        body = []
        for h in self._hits(periods):
            p = h["period"]
            body.append(self._format_period(p))
        return body

    def timeline(self, run: str, **kwargs) -> dict[str, Any]:
        """Report the relative timeline of a run

        With nested object lists, show runs to iterations to samples to
        periods.

        Args:
            run: run ID
            kwargs: additional OpenSearch parameters
        """
        itr = self.search(
            index="iteration",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        sam = self.search(
            index="sample",
            filters=[{"term": {"run.id": run}}],
            **kwargs,
            ignore_unavailable=True,
        )
        per = self.search(
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
                robj["begin"] = self._date(i["run"]["begin"])
                robj["end"] = self._date(i["run"]["end"])
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

    def metrics_list(self, run: str, **kwargs) -> dict[str, Any]:
        """Return a list of metrics available for a run

        Each run may have multiple performance metrics stored. This API allows
        retrieving a sorted list of the metrics available for a given run, with
        the "names" selection criteria available for each and, for "periodic"
        (benchmark) metrics, the defined periods for which data was gathered.

        {
            "ilab::train-samples-sec": {
                "periods": [{"id": <id>, "name": "measurement"}],
                "names": {"benchmark-group" ["unknown"], ...}
            },
            "iostat::avg-queue-length": {
                "periods": [],
                "names": {"benchmark-group": ["unknown"], ...},
            },
            ...
        }

        Args:
            run: run ID

        Returns:
            List of metrics available for the run
        """
        hits = self.search(
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
                record = {"periods": [], "breakdowns": defaultdict(set)}
                met[name] = record
            if "period" in h:
                record["periods"].append(h["period"]["id"])
            for n, v in desc["names"].items():
                record["breakdowns"][n].add(v)
        return met

    def metric_breakouts(
        self,
        run: str,
        metric: str,
        names: Optional[list[str]] = None,
        periods: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Help explore available metric breakdowns

        Args:
            run: run ID
            metric: metric label (e.g., "mpstat::Busy-CPU")
            names: list of name filters ("cpu=3")
            periods: list of period IDs

        Returns:
            A description of all breakdown names and values, which can be
            specified to narrow down metrics returns by the data, summary, and
            graph APIs.

            {
                "label": "mpstat::Busy-CPU",
                "class": [
                    "throughput"
                ],
                "type": "Busy-CPU",
                "source": "mpstat",
                "breakdowns": {
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
        filters = self._filter_metric_desc(run, metric, names, periods)
        metric_name = metric + ("" if not names else ("+" + ",".join(names)))
        metrics = self.search(
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

    def metrics_data(
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
                    "end": "2024-09-12 18:27:15+00:00",
                    "value": 0.0,
                    "duration": 15.0
                },
                {
                    "end": "2024-09-12 18:27:30+00:00",
                    "value": 0.0007,
                    "duration": 15.0
                },
                {
                    "end": "2024-09-12 18:27:45+00:00",
                    "value": 0.0033,
                    "duration": 15.0
                }
            ]
        """
        start = time.time()
        ids = self._get_metric_ids(
            run, metric, names, periodlist=periods, highlander=(not aggregate)
        )

        # If we're searching by periods, filter metric data by the period
        # timestamp range rather than just relying on the metric desc IDs as
        # we also want to filter non-periodic tool data.
        filters = [{"terms": {"metric_desc.id": ids}}]
        filters.extend(self._data_range(periods))

        response = []
        if len(ids) > 1:
            # Find the minimum sample interval of the selected metrics
            aggdur = self.search(
                "metric_data",
                size=0,
                filters=filters,
                aggregations={"duration": {"stats": {"field": "metric_data.duration"}}},
            )
            interval = int(aggdur["aggregations"]["duration"]["min"])
            data = self.search(
                index="metric_data",
                size=0,
                filters=filters,
                aggregations={
                    "interval": {
                        "histogram": {"field": "metric_data.end", "interval": interval},
                        "aggs": {"value": {"sum": {"field": "metric_data.value"}}},
                    }
                },
            )
            for h in self._aggs(data, "interval"):
                response.append(
                    {
                        "begin": self._date(h["key"] - interval),
                        "end": self._date(h["key"]),
                        "value": h["value"]["value"],
                        "duration": interval / 1000.0,
                    }
                )
        else:
            data = self.search("metric_data", filters=filters)
            for h in self._hits(data, ["metric_data"]):
                response.append(self._format_data(h))
        response.sort(key=lambda a: a["end"])
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
        return response

    def metrics_summary(
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
                "sum": 1.6761000000000001
            }
        """
        start = time.time()
        ids = self._get_metric_ids(run, metric, names, periodlist=periods)
        filters = [{"terms": {"metric_desc.id": ids}}]
        filters.extend(self._data_range(periods))
        data = self.search(
            "metric_data",
            size=0,
            filters=filters,
            aggregations={"score": {"stats": {"field": "metric_data.value"}}},
        )
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
        return data["aggregations"]["score"]

    def metrics_graph(self, graphdata: GraphList) -> dict[str, Any]:
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
        run = graphdata.run
        layout: dict[str, Any] = {"width": "1500"}
        axes = {}
        yaxis = None
        cindex = 0
        for g in graphdata.graphs:
            names = g.names
            metric: str = g.metric
            ids = self._get_metric_ids(
                run, metric, names, periodlist=g.periods, highlander=(not g.aggregate)
            )
            filters = [{"terms": {"metric_desc.id": ids}}]
            filters.extend(self._data_range(g.periods))
            y_max = 0.0
            points = []

            # If we're pulling multiple breakouts, e.g., total CPU across modes
            # or cores, we want to aggregate by timestamp. (Note that this will
            # not work well unless the samples are aligned.)
            if len(ids) > 1:
                # Find the minimum sample interval of the selected metrics
                aggdur = self.search(
                    "metric_data",
                    size=0,
                    filters=filters,
                    aggregations={
                        "duration": {"stats": {"field": "metric_data.duration"}}
                    },
                )
                interval = int(aggdur["aggregations"]["duration"]["min"])
                data = self.search(
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
                    points.append((h["key"], h["value"]["value"]))
            else:
                data = self.search("metric_data", filters=filters)
                for h in self._hits(data, ["metric_data"]):
                    points.append((h["end"], float(h["value"])))

            # Graph the "end" timestamp of each sample against the sample
            # value. Sort the graph points by timestamp so that Ploty will draw
            # nice lines.
            x = []
            y = []

            for t, v in sorted(points):
                x.append(self._date(t))
                y.append(v)
                y_max = max(y_max, v)

            try:
                options = " " + ",".join(names) if names else ""
                title = metric + options

                # TODO -- how to identify the period here? Can I filter out
                # param differences to label these based on the batch size??
                graphitem = {
                    "x": x,
                    "y": y,
                    "name": title,
                    "type": "scatter",
                    "mode": "line",
                    "marker": {"color": colors[cindex]},
                    "labels": {
                        "x": "sample timestamp",
                        "y": "samples / second",
                    },
                }

                # Y-axis scaling and labeling is divided by benchmark label;
                # so store each we've created to reuse. (E.g., if we graph
                # 5 different mpstat::Busy-CPU periods, they'll share a single
                # Y axis.)
                if title in axes:
                    yref = axes[metric]
                else:
                    if yaxis:
                        name = f"yaxis{yaxis}"
                        yref = f"y{yaxis}"
                        yaxis += 1
                        layout[name] = {
                            "title": title,
                            "color": colors[cindex],
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
                            "title": title,
                            "color": colors[cindex],
                        }
                    axes[metric] = yref
                graphitem["yaxis"] = yref
                cindex += 1
                if cindex >= len(colors):
                    cindex = 0
                graphlist.append(graphitem)
            except ValueError as v:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected data type: {str(v)}",
                )
        duration = time.time() - start
        print(f"Processing took {duration} seconds")
        return {"data": graphlist, "layout": layout}

    def fields(self, index: str) -> dict[str, set]:
        """Return the fields of an OpenSearch document from an index

        This fetches the document mapping from OpenSearch and reports it as a
        set of subfields for each primary field.

        {
            "cdm": [
                "ver"
            ],
            "metric_data": [
                "begin",
                "value",
                "end",
                "duration"
            ],
            "metric_desc": [
                "id"
            ]
        }

        This is mostly useful while developing additional APIs against the
        Crucible CDM.

        Args:
            index:  Root name of index (e.g., "run")

        Returns:
            Document layout, like {"cdm": ["ver"], "metric_data": ["begin", "value", ...]}
        """
        try:
            idx = self._get_index(index)
            mapping = self.elastic.indices.get_mapping(index=idx)
            fields = defaultdict(set)
            for f, subfields in mapping[idx]["mappings"]["properties"].items():
                for s in subfields["properties"].keys():
                    fields[f].add(s)
            return fields
        except NotFoundError:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Index name {index!r} doesn't exist"
            )
