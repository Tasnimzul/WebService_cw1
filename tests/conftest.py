from unittest.mock import patch

# Patch slowapi's rate limit check to always pass during tests
@patch("slowapi.extension.Limiter._check_request_limit", return_value=None)
def pytest_configure(config, mock_check=None):
    pass