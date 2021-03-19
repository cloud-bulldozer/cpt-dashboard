from pydantic import BaseModel


class Timesrange(BaseModel):
    format: str
    gte: str = 'now-3M'
    lte: str = 'now'


class Timestamp(BaseModel):
    timestamp: Timesrange


class Range(BaseModel):
    range: Timestamp


class Query(BaseModel):
    query: Range

