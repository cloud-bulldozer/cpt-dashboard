from vyper import v


def get_config():
    v.set_config_name('ocpperf')
    v.add_config_path('.')
    v.read_in_config()
    return v
