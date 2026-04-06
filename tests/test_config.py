"""Tests for config loading and validation."""

import os
import tempfile

import pytest
import yaml

from src.config import load_config


def _write_config(data: dict) -> str:
    """Write config data to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(data, f)
    f.close()
    return f.name


def _minimal_config(**overrides):
    """Return a minimal valid config dict."""
    config = {
        "tickers": ["AAPL", "NVDA"],
        "email": {"to": "user@example.com", "from": "sender@example.com"},
        "edgar": {"user_agent": "Test test@example.com"},
    }
    config.update(overrides)
    return config


class TestConfigLoading:
    def test_valid_config(self):
        path = _write_config(_minimal_config())
        config = load_config(path)
        assert config["tickers"] == ["AAPL", "NVDA"]
        assert config["email"]["to"] == "user@example.com"
        os.unlink(path)

    def test_defaults_applied(self):
        path = _write_config(_minimal_config())
        config = load_config(path)
        assert config["edgar"]["lookback_days"] == 7
        assert config["pricing"]["history_days"] == 5
        os.unlink(path)

    def test_missing_tickers(self):
        data = _minimal_config()
        del data["tickers"]
        path = _write_config(data)
        with pytest.raises(ValueError, match="Missing required config field: tickers"):
            load_config(path)
        os.unlink(path)

    def test_missing_email_to(self):
        data = _minimal_config()
        del data["email"]["to"]
        path = _write_config(data)
        with pytest.raises(ValueError, match="Missing required config field: email.to"):
            load_config(path)
        os.unlink(path)

    def test_empty_tickers(self):
        path = _write_config(_minimal_config(tickers=[]))
        with pytest.raises(ValueError, match="must not be empty"):
            load_config(path)
        os.unlink(path)

    def test_invalid_ticker_format(self):
        path = _write_config(_minimal_config(tickers=["AAPL", "bad ticker"]))
        with pytest.raises(ValueError, match="Invalid ticker"):
            load_config(path)
        os.unlink(path)

    def test_env_override_api_key(self):
        path = _write_config(_minimal_config())
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-key"
        try:
            config = load_config(path)
            assert config["anthropic"]["api_key"] == "sk-test-key"
        finally:
            del os.environ["ANTHROPIC_API_KEY"]
            os.unlink(path)

    def test_env_override_email(self):
        path = _write_config(_minimal_config())
        os.environ["EMAIL_TO"] = "override@example.com"
        try:
            config = load_config(path)
            assert config["email"]["to"] == "override@example.com"
        finally:
            del os.environ["EMAIL_TO"]
            os.unlink(path)
