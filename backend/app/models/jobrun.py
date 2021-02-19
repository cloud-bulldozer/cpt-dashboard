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
  cluster_version: str
  platform: str
  network_type: str
  # build_date: date
  timestamp: datetime
  job_name: str
  # build_number: PositiveInt
  build_number: Optional[PositiveInt] = None
  # workload: str
  job_status: str
  result: Optional[IPv4Address] = None
  build_tag: str
