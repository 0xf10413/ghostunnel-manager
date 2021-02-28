import logging
from time import sleep
import os
import subprocess

logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(format="[%(asctime)s] { %(threadName)s "
                          "%(filename)s:%(lineno)d} "
                          "%(levelname)s - %(message)s")

GHOSTMANAGER_TARGETS = "GHOSTMANAGER_TARGETS"

running = True
proxy = None
targets = None

def pick_new_target():
    """
    Pick a new target from the targets file.

    Read the targets once, then cache it.
    Remove one target (and returns it) after each call.
    When all targets are removed from the cache, re-read the file.

    This way, we will eventually re-read the configuration if it changes.
    """
    global targets

    # Targets empty or not initalized => initialize it
    if not targets:
        file = os.getenv(GHOSTMANAGER_TARGETS, "")
        logging.info("Opening targets file %r (read from %s)", file, GHOSTMANAGER_TARGETS)
        try:
            with open(file, 'r') as f:
                targets = [ f"{t.strip()}:443" for t in f.readlines()]
        except OSError:
            logging.exception("Can't read targets file, please check your configuration")
            raise

    # Targets still empty => should not happen
    if not targets:
        logging.error("Targets file read, but contained no lines. Please check your configuraiton.")
        raise RuntimeError("No line in targets file")

    # Just pick the first one and remove it from the list.
    return targets.pop()

def run_health_check(target):
    # TODO: another kind of test !
    import requests as rq
    try:
        return rq.get(f"https://{target}").status_code in [200, 301, 302]
    except rq.RequestException as e:
        logging.error("Health check failed with error: %s", e)
        return False

def spawn_proxy(target):
    proxy = subprocess.Popen([
        "/home/flo/documents/code/python-ghostunnel-manager/ghostunnel",
        "client",
        "--target",
        target,
        "--listen",
        "localhost:8082",
        "--disable-authentication",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proxy


def is_alive(proxy):
    return proxy.returncode is None

def shutdown_proxy(proxy):
    logging.info("Closing proxy")

    try:
        proxy.wait(1)
        logging.info("stdout was %s, %s", proxy.stdout.read(), proxy.returncode)
    except subprocess.TimeoutExpired:
        logging.warning("Got timeout after waiting for proxy wait()")


    proxy.terminate()
    try:
        proxy.wait(1)
        logging.info("stdout was %s, %s", proxy.stdout.read(), proxy.returncode)
        return
    except subprocess.TimeoutExpired:
        logging.warning("Got timeout after waiting for proxy terminate()")

    proxy.kill()
    try:
        proxy.wait(1)
        return
    except subprocess.TimeoutExpired:
        loggin.error("Got timeout after waiting for proxy kill(). Something was probably leaked.")


# Note: no try/catch, so any exception will kill the program
while running:
    # Choose a new target
    target = pick_new_target()
    logging.info("Picked new target %s", target)

    while run_health_check(target):
        # If we haven't done it yet, spawn proxy over the target
        if proxy is None:
            proxy = spawn_proxy(target)
            logging.info("Proxy spawned")
        
        # Check that proxy is still alive
        if not is_alive(proxy):
            logging.warning("Proxy not alive, there is an issue with this target. Changing target.")
            break

        # At this point, we have nothing to do
        logging.debug("Nothing to do, sleeping")
        sleep(10)

    # If we reached this point, then the proxy needs to be reset
    if proxy is not None:
        shutdown_proxy(proxy)
        proxy = None

    logging.info("Spam protection - waiting before picking a new target")
    sleep(10)


