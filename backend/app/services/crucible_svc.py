"""Service to pull data from a Crucible CDM OpenSearch data store

A set of helper methods to enable a project API to easily process data from a
Crucible controller's OpenSearch data backend.

This includes paginated, filtered, and sorted lists of benchmark runs, along
access to the associated Crucible documents such as iterations, samples, and
periods. Metric data can be accessed by breakout names, or aggregated by
breakout subsets or collection periods as either raw data points, statistical
aggregate, or Plotly graph format for UI display.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
import time
from typing import Any, Callable, Iterator, Optional, Tuple, Union

from dateutil import rrule
from dateutil.relativedelta import relativedelta
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException, status
from pydantic import BaseModel

from app import config


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


class DTOField:
    """Define a field type for the DTO classes

    Three separate names are possible, by default all the same.

    Normally, they're all identical; however when the CDM field name uses a
    hyphen, we substitute an understore; and when the attribute name is a
    Python reserved word ("class"), we rename the attribute but "un-rename"
    the serialized DTO JSON. In a few cases, we want to convert the raw
    CDM field type from string.

    attr: The name of the DTO class attribute
    field: The name of the CDM JSON field, if different
    name: The name of the serialized DTO field, if different
    type: Type conversion from CDM to DTO
    synthetic: Skip on input conversion, but serialize on output
    """

    attr: str
    field: str
    name: str
    type: Optional[Callable[[str], Any]]
    synthetic: Any

    def __init__(
        self,
        attr: str,
        field: Optional[str] = None,
        name: Optional[str] = None,
        type: Optional[Callable[[str], Any]] = None,
        synthetic: Any = None,
    ):
        self.attr = attr
        self.field = field if field else attr
        self.name = name if name else attr
        self.type = type
        self.synthetic = synthetic


@dataclass
class FullID:
    """Decode an extended record ID

    To facilitate optimized queries, externally visible CDM record IDs (run,
    iteration, and sample) are annoted to enable us to determine the precise
    CDM index we need to query for subsidiary information (iteration, sample,
    period, params, tags, metric desc & data) relating to that ID. That's
    because the timeseries suffix (@YYYY.MM) and index version will always
    match. E.g., for a run in cdm-v9dev-run@2025-06 all metric data captured
    for that run will be in cdm-v9dev-metric_data@2025-06.

    This class is used to decode that extended ID, which looks like
    <uuid>@v9dev@2025-06, to get the index qualifiers (version and date) along
    with the original CDM document UUID.
    """

    id: str
    version: Optional[str] = None
    date: Optional[str] = None

    @classmethod
    def decode(cls, id: Union["FullID", str]) -> "FullID":
        if isinstance(id, FullID):
            return id
        pieces = id.split("@", maxsplit=2)
        return FullID(
            pieces[0],
            pieces[1] if len(pieces) > 1 and pieces[1] else None,
            pieces[2] if len(pieces) > 2 and pieces[2] else None,
        )

    def render(self) -> str:
        if self.version or self.date:
            return (
                f"{self.id}@{self.version if self.version else ''}"
                f"@{self.date if self.date else ''}"
            )
        else:
            return self.id


class DTO:
    version: str
    is_raw: bool

    TYPE: str = ""
    TOPKEYS = frozenset(("_source", "_index"))
    FIELDS = ()

    def __init__(self, raw: dict[str, Any]):
        """Construct a DTO from a OpenSearch 'hit'

        The "raw" payload can be either the hit itself, containing both
        "_source" and "_index" keys, or it can be the "_source" value.
        In the former case, the actual CDM object UUID will be recorded
        in "self.uuid" but "self.id" will combine that UUID with the
        CDM version (e.g. "v9dev") and the timeseries index suffix (e.g.,
        "@2025.05"). This is used for RunDTO so we know how to construct
        the index pattern for subsequent queries using the id. E.g.,
        /api/v1/ilab/runs/<id>@v9dev@2025.05/iterations knows to look in the
        index named cdm-v9dev-iteration@2025.05 rather than searching all
        indices.

        Args:
            raw: the OpenSearch response["hits"]["hits"] element, or the
                "_source" subdocument of that hit
        """
        self.is_raw = False
        if self.TOPKEYS.issubset(set(raw.keys())):
            raw = raw["_source"]
            self.is_raw = True
        req_keys = {"cdm", self.TYPE}
        act_keys = set(raw.keys())
        if not req_keys.issubset(act_keys):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Raw CDM object is missing required keys: "
                f"{sorted(req_keys - act_keys)} not in {sorted(act_keys)}",
            )
        self.version = raw["cdm"]["ver"]
        s = raw[self.TYPE]
        for f in self.FIELDS:
            if f.synthetic is not None:
                v = f.synthetic() if isinstance(f.synthetic, Callable) else f.synthetic
            else:
                v = s.get(f.field)
                if v and f.type:
                    v = f.type(v)
            setattr(self, f.attr, v)

    def _amend(self, json: dict[str, Any]):
        """Allow subclasses to extend or modify the JSON

        For example, to translate types for consistency, add formatted
        dates, etc.

        The base class implementation does nothing.
        """
        pass

    def json(self) -> dict[str, Any]:
        """Render the DTO object as JSON for transport

        This will implicitly perform some conversions on fields:

        * defaultdicts (used to collect k/v pairs) become dicts
        * sets become sorted lists
        * lists of DTOs with ID are `json`-ed and sorted by ID

        Returns:
            JSON dict
        """
        serial: dict[str, Any] = {}
        for f in self.FIELDS:
            v = getattr(self, f.attr)

            # Do some automated cleanup type conversions, including serializing
            # and sorting lists of DTO objects.
            if isinstance(v, defaultdict):
                v = {key: val for key, val in v.items()}
            elif isinstance(v, set):
                v = sorted(v)
            elif isinstance(v, list) and len(v) and isinstance(v[0], DTOId):
                v = [i.json() for i in sorted(v, key=lambda i: i.uuid)]
            serial[f.name] = v
        self._amend(serial)
        return serial


class DTOId(DTO):
    """Extend the DTO with an 'id'

    Most CDM documents have a uuid field. We capture both the uuid and the
    index in which the document was found (if we're given a "raw" OpenSearch
    hit), constructing an "id" from the uuid combined with the index version
    and date. This allows optimized queries when given an ID: for example,
    for "<uuid>@v9dev@2025.05" we know all associated iterations with run
    uuid <uuid> will be found in index "cdm-v9dev-iteration@2025.05".
    """

    location: FullID
    uuid: str

    FIELDS: tuple[DTOField, ...] = (
        DTOField("id", synthetic=True),
        DTOField("uuid"),
    )
    INDEXRE = re.compile(r"cdm-?(?P<ver>v\d+dev)-\w+(@(?P<date>\d{4}\.\d{2}))?")

    def id_name(self) -> str:
        """Identify the name of the 'uuid' field

        A CDM record's UUID is "<root>-uuid" ("run-uuid", "iteration-uuid",
        etc.)
        """
        return f"{self.TYPE}-uuid"

    def __init__(self, raw: dict[str, Any]):
        """Capture the index if we can"""
        super().__init__(raw)
        s = (raw["_source"] if self.is_raw else raw)[self.TYPE]
        self.uuid = s[self.id_name()]
        self.location = FullID(self.uuid)
        index = None
        if self.is_raw:
            index = raw["_index"]
            match = self.INDEXRE.match(index)
            if match:
                self.location = FullID(
                    self.uuid, match.group("ver"), match.group("date")
                )

    def json(self) -> dict[str, Any]:
        return {"id": self.location.render(), "uuid": self.uuid} | super().json()


class RunDTO(DTOId):
    """Run index document DTO"""

    begin: int
    end: int
    benchmark: Optional[str]
    email: Optional[str]
    name: Optional[str]
    source: Optional[str]
    status: Optional[str]
    iterations: list["IterationDTO"]
    tags: dict[str, Any]
    params: dict[str, Any]
    primary_metrics: set[str]

    TYPE: str = "run"
    FIELDS = (
        DTOField("begin", type=int),
        DTOField("end", type=int),
        DTOField("benchmark"),
        DTOField("email"),
        DTOField("name"),
        DTOField("source"),
        DTOField("status", synthetic=None),
        DTOField("harness", synthetic=None),
        DTOField("host", synthetic=None),
        DTOField("iterations", synthetic=list),
        DTOField("tags", synthetic=dict),
        DTOField("params", synthetic=dict),
        DTOField("primary_metrics", synthetic=set),
    )

    def _amend(self, json: dict[str, Any]):
        json["begin_date"] = CrucibleService._format_timestamp(self.begin)
        json["end_date"] = CrucibleService._format_timestamp(self.end)


class IterationDTO(DTOId):
    """Iteration index document DTO"""

    num: int
    path: str
    primary_metric: str
    primary_period: str
    status: str
    params: str

    TYPE: str = "iteration"
    FIELDS = (
        DTOField("num"),
        DTOField("path"),
        DTOField("status"),
        DTOField("primary_metric", "primary-metric"),
        DTOField("primary_period", "primary-period"),
        DTOField("params", synthetic=dict),
    )


class SampleDTO(DTOId):
    """Sample index document DTO"""

    num: int
    path: str
    status: str
    iteration: int
    primary_metric: str
    primary_period: str

    TYPE: str = "sample"
    FIELDS = (
        DTOField("num", type=int),
        DTOField("path"),
        DTOField("status"),
        DTOField("iteration"),
        DTOField("primary_metric"),
        DTOField("primary_period"),
    )

    def __init__(self, raw: dict[str, Any]):
        """Extend the DTO constructor

        For convenience, we extend the CDM sample to include identifying info
        from the iteration.
        """
        super().__init__(raw)
        src = raw.get("_source", raw)
        self.iteration = src["iteration"]["num"]
        self.primary_metric = src["iteration"]["primary-metric"]
        self.primary_period = src["iteration"]["primary-period"]


class PeriodDTO(DTOId):
    """Period index document DTO"""

    begin: int
    end: int
    name: str
    iteration: int
    sample: str
    primary_metric: str
    is_primary: bool
    status: str

    TYPE: str = "period"
    FIELDS = (
        DTOField("begin", type=int),
        DTOField("end", type=int),
        DTOField("name"),
        DTOField("iteration"),
        DTOField("sample"),
        DTOField("primary_metric"),
        DTOField("is_primary"),
        DTOField("status"),
    )

    def __init__(self, raw: dict[str, Any]):
        """Extend the DTO constructor

        For convenience, we extend the CDM period to include identifying info
        from the iteration and sample.
        """
        super().__init__(raw)
        src = raw.get("_source", raw)
        self.iteration = src["iteration"]["num"]
        self.sample = src["sample"]["num"]
        is_primary = src["iteration"]["primary-period"] == src["period"]["name"]
        self.is_primary = is_primary
        if is_primary:
            self.primary_metric = src["iteration"]["primary-metric"]
        self.status = src["iteration"]["status"]

    def _amend(self, json: dict[str, Any]):
        json["begin_date"] = CrucibleService._format_timestamp(self.begin)
        json["end_date"] = CrucibleService._format_timestamp(self.end)


class MetricDTO(DTOId):
    """Metric descriptor index document DTO"""

    metric_class: str
    names: dict[str, Any]
    names_list: list[str]
    source: str
    type: str

    TYPE: str = "metric_desc"
    FIELDS = (
        DTOField("metric_class", "class", "class"),
        DTOField("names"),
        DTOField("names_list", "names-list"),
        DTOField("source"),
        DTOField("type"),
    )


class DataDTO(DTO):
    """Metric data index document DTO"""

    begin: int
    duration: float
    end: int
    value: float

    TYPE: str = "metric_data"
    FIELDS = (
        DTOField("begin", type=int),
        DTOField("duration", type=lambda x: (int(x) / 1000.0)),
        DTOField("end", type=int),
        DTOField("value", type=float),
    )

    def _amend(self, json: dict[str, Any]):
        """Format the timestamps

        In other cases, we leave the integer timestamps and create new fields
        with the formatted time string. In this case, we replace them as Plotly
        won't recognize the type of the integer form, and we want to keep the
        (potentially large) array of data points as relatively lean as we can.
        """
        json["begin"] = CrucibleService._format_timestamp(self.begin)
        json["end"] = CrucibleService._format_timestamp(self.end)


class CrucibleService:
    """Support convenient generalized access to Crucible data

    This implements access to the Crucible "Common Data Model" (versions 7 and 8)
    through OpenSearch queries.
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
        self.versions = set()
        self.elastic = AsyncElasticsearch(self.url, http_auth=self.auth)
        self.logger.info("Initializing CDM service to %s", self.url)

    async def detect_versions(self):
        """Determine which CDM versions are present on the server

        This is a bit tricky: because we're using the Async OpenSearch client,
        we need to "await" the response, which we can't do in the synchronous
        constructor, so we do it dynamically when needed, to compute a full
        index name.
        """
        if not self.versions:
            indices = await self.elastic.indices.get(
                "cdm*-run*", allow_no_indices=True, ignore_unavailable=True
            )
            versions = set()
            vpat = re.compile(r"cdm-?(?P<version>v\d+dev)-")
            for i in indices.keys():
                match = vpat.match(i)
                if match:
                    try:
                        versions.add(match.group("version"))
                    except Exception as e:
                        self.logger.debug(f"Skipping index {i}: {str(e)!r}")
            self.versions = versions

    async def _get_index(
        self,
        root: str,
        begin: Optional[str] = None,
        end: Optional[str] = None,
        ref_id: Optional[Union[FullID, str]] = None,
    ) -> str:
        """Construct an index string for a query

        This may resolve to a single index, fully qualified ("cdmv8dev-run") or
        to a list of indices, possibly with wildcards, like "cdm-v9dev-run@*",
        or "cdm-v9dev-run@2025.04,cdm-v9dev-run@2025.05", depending on the CDM
        version and parameters.

        Args:
            root: root index name (run, iteration, etc.)
            begin: a begin date if we have a range
            end: an end date if we have a range
            ref_id: a fully qualified object ID providing version and date

        Returns:
            the index portion of an OpenSearch query URL
        """
        version = None
        date = None
        index_string = None
        if ref_id:
            ri = FullID.decode(ref_id)
            version = ri.version
            date = ri.date

        # If we have a reference ID, we lock the index to that reference
        if version and date:
            index_string = f"cdm-{version}-{root}@{date}"
        elif version and version < "v9dev":
            index_string = f"cdm{version}-{root}"
        else:
            # No reference ID, so we need to analyze the CDM indices available
            await self.detect_versions()
            indices = set()
            for version in self.versions:
                if version < "v9dev":
                    indices.add(f"cdm{version}-{root}")
                elif not begin:
                    # A missing begin date could result in hundreds of indices
                    # that don't exist, making an impractically long URL.
                    # Instead, fall back to a wildcard pattern.
                    indices.add(f"cdm-{version}-{root}@*")
                else:
                    e = end if end else datetime.now(timezone.utc).isoformat()
                    first_month = (datetime.fromisoformat(begin)).replace(day=1)
                    last_month = datetime.fromisoformat(e) + relativedelta(day=31)
                    for m in rrule.rrule(
                        rrule.MONTHLY, dtstart=first_month, until=last_month
                    ):
                        indices.add(f"cdm-{version}-{root}@{m.year:04}.{m.month:02}")
            index_string = ",".join(indices)
        return index_string

    def _get_id_field(self, root: str) -> str:
        """Get the versioned name of the CDM uuid field for an index"""
        return f"{root}-uuid"

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

    @classmethod
    def _split_id_list(cls, alist: Optional[list[str]] = None) -> list[FullID]:
        """Split a list of object ID parameters

        This builds on _split_list above to process each element of the
        resulting list as an ID (<uuid>@<version>@<date>).

        Args:
            alist: list of IDs

        Returns:
            List of FullID objects
        """
        l: list[str] = cls._split_list(alist)
        return [FullID.decode(i) for i in l]

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
        cls,
        payload: dict[str, Any],
        fields: Optional[list[str]] = None,
        raw: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Helper to iterate through OpenSearch query matches

        Iteratively yields the "_source" of each hit. As a convenience, can
        yield a sub-object of "_source" ... for example, specifying the
        optional "fields" as ["metric_desc", "id"] will yield the equivalent of
        hit["_source"]["metric_desc"]["id"]

        Args:
            payload: OpenSearch reponse payload
            fields: Optional sub-fields of "_source"
            raw: Return the entire hit

        Returns:
            Yields each object from the "greatest hits" list
        """
        if "hits" not in payload or not isinstance(payload["hits"], dict):
            raise HTTPException(
                status_code=500, detail=f"Attempt to iterate hits for {payload}"
            )
        hits = cls._get(payload, ["hits", "hits"], [])
        for h in hits:
            if raw:
                yield h
            else:
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
        pl: list[FullID] = self._split_id_list(periodlist)
        pidn = self._get_id_field("period")
        if pl:
            return [
                {
                    "dis_max": {
                        "queries": [
                            {"bool": {"must_not": {"exists": {"field": "period"}}}},
                            {"terms": {f"period.{pidn}": [i.id for i in pl]}},
                        ]
                    }
                }
            ]
        else:
            return []

    def _build_metric_filters(
        self,
        run: Union[FullID, str],
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
        full_id = FullID.decode(run)
        return (
            [
                {"term": {f"run.{ridn}": full_id.id}},
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

    async def close(self):
        """Close the OpenSearch connection"""
        if self.elastic:
            await self.elastic.close()
        self.elastic = None

    async def search(
        self,
        index: str,
        begin: Optional[str] = None,
        end: Optional[str] = None,
        ref_id: Optional[Union[FullID, str]] = None,
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
            begin: begin timestamp
            end: end timestamp
            ref_id: a FullID object to constrain secondary index queries
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
        idx = await self._get_index(index, begin=begin, end=end, ref_id=ref_id)
        start = time.time()
        value = await self.elastic.search(index=idx, body=query, **kwargs)
        self.logger.info(
            "QUERY on %s took %.3f seconds, hits: %d",
            idx,
            time.time() - start,
            value.get("hits", {}).get("total"),
        )
        return value

    async def _get_metric_ids(
        self,
        run: Union[FullID, str],
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
            ref_id=run,
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
            ps: list[FullID] = self._split_id_list(periods)
            pidn = self._get_id_field("period")
            matches = await self.search(
                "period", filters=[{"terms": {f"period.{pidn}": [p.id for p in ps]}}]
            )
            if len(matches["hits"]["hits"]) != len(ps):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot find all of the periods in {ps}",
                )
            try:
                start = min([int(h) for h in self._hits(matches, ["period", "begin"])])
                end = max([int(h) for h in self._hits(matches, ["period", "end"])])
            except Exception as e:
                plist = ",".join([p.render() for p in ps])
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
        return set([x for x in self._hits(filtered, ["run", ridn])])

    async def _make_title(
        self,
        run: Union[FullID, str],
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
        run_id = FullID.decode(run)
        if run_id.id not in params_by_run:
            # Gather iteration parameters outside the loop for help in
            # generating useful labels.
            all_params = await self.search(
                "param", ref_id=run_id, filters=[{"term": {f"run.{ridn}": run_id.id}}]
            )
            collector = defaultdict(defaultdict)
            for h in self._hits(all_params):
                collector[h["iteration"][iidn]][h["param"]["arg"]] = h["param"]["val"]
            params_by_run[run_id.id] = collector
        else:
            collector = params_by_run[run_id.id]

        if run_id.id not in periods_by_run:
            periods = await self.search(
                "period", ref_id=run_id, filters=[{"term": {f"run.{ridn}": run_id.id}}]
            )
            iteration_periods = defaultdict(list[dict[str, Any]])
            for p in self._hits(periods):
                iteration_periods[p["iteration"][iidn]].append(p["period"])
            periods_by_run[run_id.id] = iteration_periods
        else:
            iteration_periods = periods_by_run[run_id.id]

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
            name_suffix += f" {{run {run_id_list.index(run_id.id) + 1}}}"

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
                    "source": "<host>/<path>/<name>--<date>--<uuid>",
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
        start_date = None
        end_date = None
        if start or end:
            self.logger.info(f"Filtering runs from {start} to {end}")
            s = None
            e = None
            if start:
                s = self._normalize_date(start)
                start_date = datetime.fromtimestamp(
                    s / 1000.0, tz=timezone.utc
                ).isoformat()
                results["startDate"] = start_date
            if end:
                e = self._normalize_date(end)
                end_date = datetime.fromtimestamp(
                    e / 1000.0, tz=timezone.utc
                ).isoformat()
                results["endDate"] = end_date

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
        tagids = set()
        paramids = set()
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
            begin=start_date,
            end=end_date,
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
        ridn = self._get_id_field("run")
        iidn = self._get_id_field("iteration")

        for i in self._hits(rawiterations, raw=True):
            iterations[i["_source"]["run"][ridn]].append(IterationDTO(i))

        # Organize tags by run ID
        for t in self._hits(rawtags):
            tags[t["run"][ridn]][t["tag"]["name"]] = t["tag"]["val"]

        # Organize period timestamps by run ID
        for p in self._hits(rawperiods):
            period = PeriodDTO(p)
            rid = p["run"][ridn]
            range = periods.get(rid)
            try:
                b = period.begin
                e = period.end
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
            params[p["iteration"][iidn]][p["param"]["arg"]] = p["param"]["val"]

        runs = []
        for h in self._hits(hits, raw=True):
            run = RunDTO(h)
            rid = run.uuid

            # Filter the runs by our tag and param queries
            if param_filters and rid not in paramids:
                continue

            if tag_filters and rid not in tagids:
                continue

            if not run.begin or not run.end:
                if rid in periods:
                    b, e = periods[rid]
                    if b is None or e is None:
                        self.logger.warning(
                            f"can't find begin/end timestamps for run {rid}: ignoring"
                        )
                        continue
                    self.logger.info(
                        f"normalizing run {rid} timestamps to period ({b} -> {e})"
                    )
                    run.begin = b
                    run.end = e

            run.tags = tags.get(rid, {})
            common = CommonParams()

            # Collect unique iterations: the status is "fail" if any iteration
            # for that run ID failed.
            for i in iterations.get(rid, []):
                iparams = params.get(i.uuid, {})
                i.params = iparams
                if not run.status:
                    run.status = i.status
                else:
                    if i.status != "pass":
                        run.status = i.status
                common.add(iparams)
                run.primary_metrics.add(i.primary_metric)
                run.iterations.append(i)
            run.iterations.sort(key=lambda i: i.num)
            run.params = common.render()
            runs.append(run)

        count = len(runs)
        total = hits["hits"]["total"]["value"]
        results.update(
            {
                "results": [r.json() for r in runs],
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
        run_id = FullID.decode(run)
        ridn = self._get_id_field("run")
        tags = await self.search(
            index="tag",
            ref_id=run_id,
            filters=[{"term": {f"run.{ridn}": run_id.id}}],
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
        full_id = FullID.decode(run if run else iteration)
        match = {f"run.{ridn}" if run else f"iteration.{iidn}": (full_id.id)}
        params = await self.search(
            index="param",
            ref_id=full_id,
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
        hits = await self.search(
            index="iteration",
            ref_id=run,
            filters=[{"term": {f"run.{ridn}": FullID.decode(run).id}}],
            sort=[{"iteration.num": "asc"}],
            **kwargs,
            ignore_unavailable=True,
        )

        iterations = []
        for i in self._hits(hits, raw=True):
            iterations.append(IterationDTO(i).json())
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
        full_id = FullID.decode(run if run else iteration)
        match = {f"run.{ridn}" if run else f"iteration.{iidn}": full_id.id}
        hits = await self.search(
            index="sample",
            ref_id=full_id,
            filters=[{"term": match}],
            **kwargs,
            ignore_unavailable=True,
        )
        samples = []
        for s in self._hits(hits, raw=True):
            samples.append(SampleDTO(s).json())
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
        full_id = FullID.decode(sample if sample else iteration if iteration else run)
        if sample:
            match = {f"sample.{sidn}": full_id.id}
        elif iteration:
            match = {f"iteration.{iidn}": full_id.id}
        else:
            match = {f"run.{ridn}": full_id.id}

        # Although CDMv9 period documents appear complete, the iteration
        # sub-document is missing some fields (like primary-metric) that we
        # want to represent here. That means we need to make a separate
        # query for the actual iteration documents. We'll organize them in
        # a map by iteration ID so we can pull information as we assemble
        # the periods.
        its: dict[str, Any] = await self.search(
            "iteration",
            ref_id=full_id,
            filters=[{"term": match}],
            ignore_unavailable=True,
        )
        iterations = {i[iidn]: i for i in self._hits(its, ["iteration"])}
        periods = await self.search(
            index="period",
            ref_id=full_id,
            filters=[{"term": match}],
            sort=[{"period.begin": "asc"}],
            **kwargs,
            ignore_unavailable=True,
        )
        body = []
        for h in self._hits(periods, raw=True):
            period = PeriodDTO(h)
            it = iterations[h["_source"]["iteration"][iidn]]
            period.primary_metric = it["primary-metric"]
            body.append(period.json())
        return body

    async def get_metrics_list(
        self, run: Union[FullID, str], **kwargs
    ) -> dict[str, Any]:
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
        full_id = FullID.decode(run)
        hits = await self.search(
            index="metric_desc",
            ref_id=full_id,
            filters=[{"term": {f"run.{ridn}": full_id.id}}],
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
        run: Union[FullID, str],
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
        full_id = FullID.decode(run)
        filters = self._build_metric_filters(full_id.id, metric, names, periods)
        metric_name = metric + ("" if not names else ("+" + ",".join(names)))
        metrics = await self.search(
            "metric_desc",
            ref_id=full_id,
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
            run,
            metric,
            names,
            periodlist=periods,
            aggregate=aggregate,
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
            for h in self._hits(data):
                response.append(DataDTO(h).json())
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
            run_id = FullID.decode(s.run).id
            if run_id not in run_id_list:
                run_id_list.append(run_id)
        for summary in summaries:
            run_id = FullID.decode(summary.run)
            ids = await self._get_metric_ids(
                run_id,
                summary.metric,
                summary.names,
                periodlist=summary.periods,
                aggregate=summary.aggregate,
            )
            filters = [{"terms": {f"metric_desc.{mdidn}": ids}}]
            filters.extend(await self._build_timestamp_range_filters(summary.periods))
            data = await self.search(
                "metric_data",
                ref_id=run_id,
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
                    run_id, run_id_list, summary, params_by_run, periods_by_run
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
                "groupclick": "toggleitem",
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
            run_id = FullID.decode(g.run).id
            if run_id not in run_id_list:
                run_id_list.append(run_id)

        for g in graphdata.graphs:
            run_id = FullID.decode(g.run)
            names = g.names
            metric: str = g.metric
            run_idx = None
            if len(run_id_list) > 1:
                run_idx = f"Run {run_id_list.index(run_id.id) + 1}"

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
                    ref_id=run_id,
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
                        ref_id=run_id,
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
