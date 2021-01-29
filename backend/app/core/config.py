import os
import sys
from pathlib import Path
import configparser

from vyper import v
from environs import Env
from marshmallow.validate import Length
from typing import Optional


def vyper_config():
	# not yet sure if we want to have elasticsearch config file override option
	# env = Env()
	# env.read_env()
	# if os.getenv('OCPPERF_SERVER_CONFIG') is not None:
	# 	env.str(
	# 		'OCPPERF_SERVER_CONFIG',
	# 		validate=Length(min=1),
	# 		subset=Optional
	# 	)
	v.set_config_name('ocpperf')
	v.add_config_path('.')
	v.read_in_config()
	return v
	
	


def get_server_config():
	config_path = os.environ.get("_OCP_SERVER_CONFIG_")
	if not config_path:
		print("server config file is not specified")
		sys.exit(1)

	config = configparser.ConfigParser()

	config.read(Path(config_path))

	return config


if __name__ == '__main__':
	v2 = vyper_config()