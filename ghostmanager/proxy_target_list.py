"""
Helper classes to load and iterate over a list of targets to proxy to.
"""

import logging
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class ProxyTarget:
    """
    Designates the target a proxy should direct to.
    """
    host: str
    port: int

    def to_hostport(self) -> str:
        return f"{self.host}:{self.port}"

# TODO: make iterable ?
class ProxyTargetList:
    """
    Helper class to load a list of targets from a file, then cycle over it.
    If the file changes, the new data is eventually reloaded.

    A "targets file" looks like this:
    ```
    google.com

    something.invalid
    ```

    Empty lines are skipped over. If the file can't be read or is empty (whitespace doesn't count),
    an exception is raised. For each target, the port is assumed to be 443.
    """
    def __init__(self, filename: str):
        """
        Builds an instance iterating over the targets described in :filename.
        """
        self._filename: str = filename
        self._targets: List[ProxyTarget] = [] # lazy-initialized

    def _reload_targets(self):
        """
        Reload targets from targets file.
        """
        logging.info("Reloading targets from file %s", self._filename)
        try:
            with open(self._filename, 'r') as file:
                for line in file.readlines():
                    # Remove whitespace, ignore empty lines
                    line = line.strip()
                    if not line:
                        continue

                    # Add everything other entry, assume port is always the same.
                    self._targets.append(ProxyTarget(host=line, port=443))
        except OSError:
            logging.exception("Can't read targets file, please check your configuration")
            raise

        if not self._targets:
            logging.error("Targets file read, but contained no lines.")
            raise RuntimeError("Targets file is empty")


    def pick_new_target(self) -> ProxyTarget:
        """
        Returns a new target from the current configuration.
        """
        if not self._targets:
            self._reload_targets()

        return self._targets.pop(0)
