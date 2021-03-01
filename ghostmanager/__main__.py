"""
Specialized tool over ghostunnel to:
* Pick a target server over a dynamic configuration list
* Spawn a ghostunnel proxy towards that target
* Run health checks on that target (through the proxy)
* Kill the proxy and switch over to the next target server in case of issue
"""
from ghostmanager.proxy_target_list import ProxyTargetList
import subprocess
import time
import logging

# Install custom logger format
# TODO: make the loglevel configurable ?
logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(format="[%(asctime)s] { %(threadName)s "
                        "%(filename)s:%(lineno)d} "
                        "%(levelname)s - %(message)s")
