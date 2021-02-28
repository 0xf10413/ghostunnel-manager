"""
Specialized tool to spawn a proxy, then run a healthcheck through it.
If the healthcheck starts failing, kill the proxy and spawn another one.
Switch according to a list of targets.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ProxyTarget:
    """
    Designates the target a proxy should direct to.
    """
    host: str
    port: int

# TODO: make this a proper class, to avoid global state
targets : List[ProxyTarget] = []
def pick_new_target(filename: str) -> ProxyTarget:
    """
    Pick a new target from the targets file.

    Read the targets once, then cache it.
    Remove one target (and returns it) after each call.
    When all targets are removed from the cache, re-read the file.

    This way, we will eventually re-read the configuration if it changes.
    """
    global targets

    # Targets empty => fill it
    if not targets:
        logging.info("Opening targets file %s", filename)
        try:
            with open(filename, 'r') as f:
                for line in f.readlines():
                    # Remove whitespace, ignore empty lines
                    line = line.strip()
                    if not line:
                        continue

                    # Add everything else, assume port is 443.
                    # Note: we put it first to keep the same ordering as the file.
                    targets.insert(0, ProxyTarget(host=line, port=443))
        except OSError:
            logging.exception("Can't read targets file, please check your configuration")
            raise

    # Targets still empty => should not happen
    if not targets:
        logging.error("Targets file read, but contained no lines. Please check your configuration.")
        raise RuntimeError("Targets file is empty")

    # Just pick the first one and remove it from the list.
    return targets.pop()
