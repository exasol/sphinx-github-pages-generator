import pytest
import os
from helper_test_functions import setup_workdir


@pytest.fixture
def setup_test_env(tmp_path):
    os.chdir(tmp_path)
    user_name, user_access_token = setup_workdir()
    return user_name, user_access_token
