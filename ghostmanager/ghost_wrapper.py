"""
Tools to start, monitor and stop easily a ghostunnel instance.

Note: implemented with subprocess and not mp.Process.
See https://bugs.python.org/issue35657.
"""

import subprocess
import logging
import time
import abc
from typing import Optional

from ghostmanager.proxy_target_list import ProxyTarget

class AbstractWrapper(metaclass=abc.ABCMeta):
    """
    Contains the parts of GhostunnelWrapper that can be tested independently.
    See GhostunnelWrapper documentation.
    """
    MAX_INTERNAL_READINESS_CHECKS = 5
    DELAY_BETWEEN_READINESS_CHECKS_SECONDS = 1
    PROXY_JOIN_TIMEOUT_SECONDS = 1

    def __init__(self):
        """
        Prepare internal attributes. Do not actually start child proxy.
        """
        self._proxy: Optional[subprocess.Popen] = None

    @abc.abstractmethod
    def __enter__(self):
        """
        This method should actually start the child proxy.
        """

    @abc.abstractmethod
    def _readiness_check(self) -> bool:
        """
        This method should block until the proxy is ready, or raise an exception in case of timeout.
        """
    
    def wait_for_readiness(self):
        """
        Block until ready, or a timeout occurs.
        """
        # Wait for it to become ready
        for _ in range(self.MAX_INTERNAL_READINESS_CHECKS):
            # TODO: if dead, exit now
            if self._readiness_check():
                return
            time.sleep(self.DELAY_BETWEEN_READINESS_CHECKS_SECONDS)
        raise RuntimeError("Proxy failed to start after several checks")

    def __exit__(self, t, v, tb):
        """
        Stops child proxy.
        """
        logging.info("Shutting down proxy...")

        # Mostly used in tests, if proxy was never started, then do nothing
        if self._proxy is None:
            logging.info("Proxy was never started, doing nothing")
            return

        try:
            logging.info("Checking if proxy is already stopped...")
            stdout, stderr = self._proxy.communicate(input=None, timeout=self.PROXY_JOIN_TIMEOUT_SECONDS)
            logging.info("Stdout was: %s", stdout)
            logging.info("Stderr was: %s", stderr)
            return
        except subprocess.TimeoutExpired:
            pass

        logging.info("Terminating proxy...")
        self._proxy.terminate()

        try:
            stdout, stderr = self._proxy.communicate(input=None, timeout=self.PROXY_JOIN_TIMEOUT_SECONDS)
            logging.info("Stdout was: %s", stdout)
            logging.info("Stderr was: %s", stderr)
            return
        except subprocess.TimeoutExpired:
            pass

        logging.warning("Killing proxy...")
        try:
            stdout, stderr = self._proxy.communicate(input=None, timeout=self.PROXY_JOIN_TIMEOUT_SECONDS)
            logging.info("Stdout was: %s", stdout)
            logging.info("Stderr was: %s", stderr)
            return
        except subprocess.TimeoutExpired:
            pass

        # We shouldn't get here
        logging.critical("Proxy is still running, something was likely leaked")
        raise RuntimeError("Proxy could not be killed")



class GhostunnelWrapper(AbstractWrapper):
    """
    Wrapper around a ghostunnel instance.
    Should be used in a `with` block.
    """
    GHOSTUNNEL_LISTEN_HOST_PORT = ("localhost", 8083)

    def __init__(self, target: ProxyTarget, cacert: Optional[str] = None):
        """
        Prepares the wrapper to instantiate a ghostunnel targeting :target.
        You can optionally provide a path to a CA file with :cacert.

        The instance will only be created when entering the `with` block.
        """
        super().__init__()
        self._target: ProxyTarget = target
        self._cacert: Optional[str] = cacert

    def _readiness_check(self) -> bool:
        """
        Internal check for readiness.
        Basically, just check if the socket is opened.
        """
        _, listen_port = self.GHOSTUNNEL_LISTEN_HOST_PORT
        return (
            f":{listen_port} ".encode("ascii")
            in subprocess.run(
                ["netstat", "-ntpl"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
                ).stdout
        )

    def __enter__(self):
        """
        Spawn ghosttunnel proxy.
        This doesn't mean it will be ready, check wait_for_readiness.
        """
        # Prepare flags
        listen_host, listen_port = self.GHOSTUNNEL_LISTEN_HOST_PORT
        listen_hostport = f"{listen_host}:{listen_port}"

        flags = [
            "ghostunnel",
            "client",
            "--target",
            self._target.to_hostport(),
            "--listen",
            listen_hostport,
            "--disable-authentication", # TODO: make customizable
        ]

        if self._cacert is not None:
            flags += [
                "--cacert",
                self._cacert,
            ]

        # Start ghostunnel.
        self._proxy = subprocess.Popen(
            flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return self
