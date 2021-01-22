import os
import sys
import configparser

def get_server_config():
	config_path = os.environ.get("_OCP_SERVER_CONFIG_")
	if not config_path:
		print("server config file is not specified")
		sys.exit(1)

	config = configparser.ConfigParser()
	config.read(config_path)

	return config
