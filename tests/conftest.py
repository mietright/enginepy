import os

import pytest

from enginepy.config import config

LOCAL_DIR = os.path.dirname(__file__)


@pytest.fixture(autouse=True)
def reset_config():
    config(reload=True)
