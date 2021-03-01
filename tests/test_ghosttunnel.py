import requests as rq
import subprocess
import ssl

import pytest_httpserver.httpserver as httpserver
from pytest_mock import MockerFixture
import pytest

from ghostmanager.proxy_target_list import ProxyTarget
from ghostmanager.ghost_wrapper import GhostunnelWrapper, AbstractWrapper

# Some fixtures to define a TLS server context
@pytest.fixture(scope="session")
def httpserver_ssl_context():
    return ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)


def test_proxy_connect(httpserver: httpserver.HTTPServer):
    """
    Check that ghosttunnel can correctly proxy cleartext data (http)
    towards a TLS server.
    """
    # Set up HTTPS server
    # TODO: mTLS ? not sure if handled…
    assert httpserver.ssl_context is not None
    httpserver.ssl_context.load_cert_chain("tests/assets/server.pem", "tests/assets/server.key")
    httpserver.expect_request("/aaa").respond_with_data('bbb')
    target = ProxyTarget(host=httpserver.host, port=httpserver.port)

    with GhostunnelWrapper(target, "tests/assets/ca.pem") as g:
        g.wait_for_readiness()
        r = rq.get("http://localhost:8083/aaa")
    assert r.status_code == 200
    assert r.content == b"bbb"


def test_generic_wrapper_proxy_never_ready(mocker: MockerFixture):
    """
    Checks behaviour when proxy fails to become ready.
    """
    # Speed up tests
    mocker.patch.object(AbstractWrapper, 'DELAY_BETWEEN_READINESS_CHECKS_SECONDS', 0)

    # Build a fake proxy class that never becomes ready
    class ActualProxy(AbstractWrapper):
        def __enter__(self):
            return self

        def _readiness_check(self):
            return False

    # Check that we get a timeout
    with pytest.raises(RuntimeError) as e:
        with ActualProxy() as p:
            p.wait_for_readiness()
    assert e.value.args == ("Proxy failed to start after several checks",)


def test_generic_wrapper_proxy_never_stops(mocker: MockerFixture):
    """
    Checks behaviour when proxy never respond to stop commands.
    """
    # Speed up tests
    mocker.patch.object(AbstractWrapper, 'DELAY_BETWEEN_READINESS_CHECKS_SECONDS', 0)
    
    # Mock Popen() so that it never stops
    mocker.patch.object(subprocess.Popen, 'communicate',
        side_effect=subprocess.TimeoutExpired("cmd", 0))

    # Create fake proxy class
    class ActualProxy(AbstractWrapper):
        def __enter__(self):
            self._proxy = subprocess.Popen("/bin/true")
            return self

        def _readiness_check(self):
            return True

    # Check that we get a timeout
    with pytest.raises(RuntimeError) as e:
        with ActualProxy() as p:
            p.wait_for_readiness()
    assert e.value.args == ("Proxy could not be killed",)

def test_generic_wrapper_proxy_already_stopped(mocker: MockerFixture):
    """
    Checks behaviour when proxy dies right away.
    """
    # Create fake proxy class that dies right away
    class ActualProxy(AbstractWrapper):
        def __enter__(self):
            self._proxy = subprocess.Popen("/bin/false")
            return self

        def _readiness_check(self):
            # NB: probably IRL this would not happen
            return True

    # Ensure that communicate() is only called once
    mocker.patch.object(subprocess.Popen, 'communicate',
        return_value=(b'stdout', b'stderr'))

    with ActualProxy() as p:
        p.wait_for_readiness()

    subprocess.Popen.communicate.assert_called_once_with(input=None, timeout=1)

def test_generic_wrapper_proxy_when_not_terminating(mocker: MockerFixture):
    """
    Checks behaviour when proxy cannot be terminated, but can be killed.
    """
    # Create fake proxy class that dies right away
    class ActualProxy(AbstractWrapper):
        def __enter__(self):
            self._proxy = subprocess.Popen("/bin/true")
            return self

        def _readiness_check(self):
            return True

    # Ensure that communicate() is called three times (no action, terminate, kill).
    # Also ensure that the first two communicate() raise a timeout exception.
    mocker.patch.object(subprocess.Popen, 'communicate',
        side_effect=[
            subprocess.TimeoutExpired("cmd", 0),
            subprocess.TimeoutExpired("cmd", 0),
            (b'stdout', b'stderr'),
        ])
    mocker.patch.object(subprocess.Popen, 'terminate')

    with ActualProxy() as p:
        p.wait_for_readiness()

    subprocess.Popen.terminate.assert_called_once_with()
    subprocess.Popen.communicate.assert_has_calls([
        mocker.call(input=None, timeout=1),
        mocker.call(input=None, timeout=1),
        mocker.call(input=None, timeout=1)
    ])
