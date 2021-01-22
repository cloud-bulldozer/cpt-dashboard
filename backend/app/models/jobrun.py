from datetime import date
from ipaddress import IPv4Address
from typing import Optional
from enum import Enum

from pydantic import BaseModel, PositiveFloat, PositiveInt


class Verdict(str, Enum):
  success = 'success'
  unstable = 'unstable'
  failure = 'failure'


class JobRun(BaseModel):
  openshift: PositiveFloat
  platform: str
  network: str
  build_date: date
  run_date: date
  job: str
  build_number: PositiveInt
  workload: str
  verdict: str
  results: Optional[IPv4Address] = None
