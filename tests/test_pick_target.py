from ghostmanager import pick_new_target, ProxyTarget

import pytest


def test_pick_targets(tmp_path):
    """
    Check that we are able to pick targets from a file as expected.
    """

    # Write example data.
    # Note the blank first line, and the whitespace all around.
    # It is expected for it to be ignored.
    filename = tmp_path / "targets.txt"
    with open(filename, 'w') as f:
        f.write("""
        google.com
        something.obviously.invalid
        """)

    # We expect it to try them on the same order
    assert pick_new_target(filename) == ProxyTarget(host="google.com", port=443)
    assert pick_new_target(filename) == ProxyTarget(host="something.obviously.invalid", port=443)

    # If we keep going, it should keep giving the same stuff
    assert pick_new_target(filename) == ProxyTarget(host="google.com", port=443)
    assert pick_new_target(filename) == ProxyTarget(host="something.obviously.invalid", port=443)
    assert pick_new_target(filename) == ProxyTarget(host="google.com", port=443)

    # If we update the file, it should notice eventually
    with open(filename, 'w') as f:
        f.write("""
        something.invalid1
        something.invalid2
        """)

    assert pick_new_target(filename) == ProxyTarget(host="something.obviously.invalid", port=443)
    assert pick_new_target(filename) == ProxyTarget(host="something.invalid1", port=443)
    assert pick_new_target(filename) == ProxyTarget(host="something.invalid2", port=443)


def test_pick_targets_errors(tmp_path):
    """
    Test some error cases when picking a target.
    """

    # Run with a file that does not exist.
    # We expect the same OSError python would raise.
    with pytest.raises(OSError):
        pick_new_target("/obviously/wrong/path/targets.txt")

    
    # Run with an empty file.
    # We expect it to complain about having no data.
    filename = tmp_path / "targets.txt"
    with open(filename, 'w') as f:
        f.write(" \n    \n    \r\n   ")

    with pytest.raises(RuntimeError) as e:
        pick_new_target(filename)

    assert e.value.args == ("Targets file is empty",)
