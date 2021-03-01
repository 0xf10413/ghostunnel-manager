"""
Specialized tool over ghostunnel to:
* Pick a target server over a dynamic configuration list
* Spawn a ghostunnel proxy towards that target
* Run health checks on that target (through the proxy)
* Kill the proxy and switch over to the next target server in case of issue
"""
from ghostmanager.proxy_target_list import ProxyTargetList
from ghostmanager.ghost_wrapper import GhostunnelWrapper
import subprocess
import time
import logging

# Install custom logger format
# TODO: make the loglevel configurable ?
logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(format="[%(asctime)s] { %(threadName)s "
                        "%(filename)s:%(lineno)d} "
                        "%(levelname)s - %(message)s")

targets_list = ProxyTargetList("./targets.txt")
target = targets_list.pick_new_target()
logging.info("Picked target %s", target)

# Open ghostunnel towards that target
try:
    with GhostunnelWrapper(target) as g:
        g.wait_for_readiness()
except RuntimeError:
    logging.info("Got runtime error, will switch target")
else:
    raise RuntimeError("Should have raised")

target = targets_list.pick_new_target()
logging.info("Picked target %s", target)
with GhostunnelWrapper(target) as g:
        g.wait_for_readiness()
        logging.info("Server up and ready ! Blocking for a while...")
        time.sleep(15)
