from pydantic import BaseModel


class Timesrange(BaseModel):
    format: str
    gte: str
    lte: str


class Timestamp(BaseModel):
    timestamp: Timesrange


class Range(BaseModel):
    range: Timestamp


class Query(BaseModel):
    query: Range