"""Config loading tests."""

import tempfile
from pathlib import Path

import pytest

from grblwheel.config import load_config
from grblwheel.files import safe_filename


def test_load_config_default():
    config = load_config(None)
    assert config["server"]["port"] == 8765
    assert config["serial"]["baud"] == 115200
    assert "macros" in config


def test_load_config_from_file():
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        f.write(b"server:\n  port: 9999\n")
        f.flush()
        path = f.name
    try:
        config = load_config(path)
        assert config["server"]["port"] == 9999
    finally:
        Path(path).unlink()


def test_safe_filename():
    assert safe_filename("foo.gcode") == "foo.gcode"
    assert safe_filename("a/b/../foo.gcode") == "foo.gcode"
    # Path traversal is neutralized by taking basename
    assert safe_filename("../../../etc/passwd") == "passwd"
    assert safe_filename("") is None
    assert safe_filename("valid_name-1.ngc") == "valid_name-1.ngc"
    # Reject names with unsafe characters
    assert safe_filename("foo bar.gcode") is None
    assert safe_filename("file\x00.gcode") is None
