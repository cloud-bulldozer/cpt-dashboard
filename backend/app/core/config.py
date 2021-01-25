import os
import sys
import configparser
from pathlib import Path


def get_server_config():
	config_path = os.environ.get("_OCP_SERVER_CONFIG_")
	if not config_path:
		print("server config file is not specified")
		sys.exit(1)

	config = configparser.ConfigParser()

	config.read(Path(config_path))

	return config
