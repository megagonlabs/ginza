import tempfile
import subprocess as sp
import sys
from pathlib import Path
from functools import partial

import pytest

run_cmd = partial(sp.run, encoding="utf-8", stdout=sp.PIPE)


@pytest.fixture(scope="session")
def tmpdir() -> Path:
    with tempfile.TemporaryDirectory() as dir_name:
        yield Path(dir_name)


@pytest.fixture(scope="session", autouse=True)
def download_model() -> None:
    run_cmd([sys.executable, "-m", "pip", "install", "ja-ginza"])
    run_cmd([sys.executable, "-m", "pip", "install", "ja-ginza-electra"])
    yield
