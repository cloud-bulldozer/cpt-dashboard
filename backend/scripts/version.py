#!/usr/bin/env python3

"""Create version information JSON file

This file is created at build time and copied into the backend container so
that we can include information that's not available at runtime.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Optional

import tomllib


def do(cmd: list[str]) -> list[str]:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Command {' '.join(cmd)!r} failed: {result.stderr}")
    return [line.strip() for line in result.stdout.split("\n") if line.strip()]


def getone(cmd: list[str], if_none: Optional[str] = None) -> str:
    res = do(cmd)
    if if_none is not None and len(res) == 0:
        return if_none
    if len(res) != 1:
        raise Exception(f"Command {' '.join(cmd)!r} returned {len(res)} lines: {res}")
    return res[0]


def main():
    top = Path(getone(["git", "rev-parse", "--show-toplevel"]))
    backend = top / "backend"
    with (backend / "pyproject.toml").open("rb") as tml:
        config = tomllib.load(tml)
    version = config["project"]["version"]
    sha = getone(["git", "rev-parse", "--short", "HEAD"])
    branch = getone(["git", "branch", "--show-current"], if_none="CI")
    display = f"v{version}-{sha}"
    print(f"VERSION: {display}")
    log = do(["git", "log", "-n10", "--format=%h###%aN###%aE###%aI###%s"])
    fields = ("sha", "author", "email", "date", "title")
    vj = {
        "version": version,
        "sha": sha,
        "branch": branch,
        "display_version": display,
        "date": datetime.now(tz=timezone.utc).isoformat(),
        "changes": [{f: v for f, v in zip(fields, lg.split("###"))} for lg in log],
    }
    with (backend / "version.json").open("w") as verfile:
        json.dump(vj, fp=verfile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
