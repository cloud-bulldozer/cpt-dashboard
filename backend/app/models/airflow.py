from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Dag(BaseModel):
    dag_id: str
    tags: Optional[list] = []
    runs: Optional[list] = []
    version: str
    platform: str
    profile: str
    release_stream: str


class DagRun(BaseModel):
    conf: Optional[dict] = {}
    dag_id: str
    dag_run_id: str
    end_date: Optional[datetime] = None
    execution_date: datetime
    external_trigger: bool
    start_date: Optional[datetime] = None
    state: str



