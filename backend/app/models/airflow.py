from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional
from enum import Enum

from pydantic import BaseModel, PositiveFloat, PositiveInt


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
  