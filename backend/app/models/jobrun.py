from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional
from enum import Enum

from pydantic import BaseModel, PositiveFloat, PositiveInt


class Verdict(str, Enum):
  success = 'success'
  unstable = 'unstable'
  failure = 'failure'


class JobRun(BaseModel):
  platform: str
  cluster_version: str
  network_type: str
  timestamp: datetime
  upstream_job: str
  job_name: str
  build_tag: str
  build_number: Optional[PositiveInt] = None
  job_status: str
  result: Optional[IPv4Address] = None
  
