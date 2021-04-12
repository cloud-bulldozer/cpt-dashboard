from datetime import datetime
from ipaddress import IPv4Address
from typing import Optional
from enum import Enum

from pydantic import BaseModel, PositiveFloat, PositiveInt


class JobRun(BaseModel):
  build_tag: Optional[str] = None
  cluster_version: str
  job_name: Optional[str] = None
  job_status: str
  network_type: str
  platform: str
  result: Optional[IPv4Address] = None
  timestamp: datetime
  upstream_job: str
  upstream_job_build: str
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None
  duration: Optional[str] = None
  execution_date: datetime = None
  build_url: Optional[str] = None

  
