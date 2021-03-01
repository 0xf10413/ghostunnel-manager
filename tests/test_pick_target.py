from ghostmanager.proxy_target_list import ProxyTargetList, ProxyTarget
import pytest


def test_pick_targets(tmp_path):
    """
    Check that we are able to pick targets from a file as expected.
    """

    # Write example data.
    # Note the blank lines, and the whitespace all around.
    # It is expected for it to be ignored.
    filename = tmp_path / "targets.txt"
    with open(filename, 'w') as f:
        f.write("   google.com   \n   something.obviously.invalid \n\n""")

    targets_list = ProxyTargetList(filename)

    # We expect it to try them on the same order
    assert targets_list.pick_new_target() == ProxyTarget(host="google.com", port=443)
    assert targets_list.pick_new_target() == ProxyTarget(host="something.obviously.invalid", port=443)

    # If we keep going, it should keep giving the same stuff
    assert targets_list.pick_new_target() == ProxyTarget(host="google.com", port=443)
    assert targets_list.pick_new_target() == ProxyTarget(host="something.obviously.invalid", port=443)
    assert targets_list.pick_new_target() == ProxyTarget(host="google.com", port=443)

    # If we update the file, it should notice eventually
    with open(filename, 'w') as f:
        f.write("""
        something.invalid1
        something.invalid2
        """)

    assert targets_list.pick_new_target() == ProxyTarget(host="something.obviously.invalid", port=443)
    assert targets_list.pick_new_target() == ProxyTarget(host="something.invalid1", port=443)
    assert targets_list.pick_new_target() == ProxyTarget(host="something.invalid2", port=443)
    assert targets_list.pick_new_target() == ProxyTarget(host="something.invalid1", port=443)


def test_pick_targets_errors(tmp_path):
    """
    Test some error cases when picking a target.
    """

    # Run with a file that does not exist.
    # We expect the same OSError python would raise.
    targets_list = ProxyTargetList("/obviously/wrong/path/targets.txt")
    with pytest.raises(OSError):
        targets_list.pick_new_target()


    # Run with an empty file.
    # We expect it to complain about having no data.
    filename = tmp_path / "targets.txt"
    with open(filename, 'w') as f:
        f.write(" \n    \n    \r\n   ")

    targets_list = ProxyTargetList(filename)
    with pytest.raises(RuntimeError) as e:
        targets_list.pick_new_target()

    assert e.value.args == ("Targets file is empty",)

def test_proxy_target():
    """
    Some generic tests on ProxyTarget class
    """
    assert ProxyTarget(host="aaa", port=456).to_hostport() == "aaa:456"
