"""YAML configuration loader with schema validation and environment variable overrides."""

import os
import re
import yaml


REQUIRED_FIELDS = {
    "tickers": list,
    "email.to": str,
    "email.from": str,
}

DEFAULTS = {
    "edgar.lookback_days": 7,
    "edgar.max_content_length": 50000,
    "edgar.filing_types": ["8-K", "10-Q", "10-K", "4"],
    "pricing.history_days": 5,
    "anthropic.model": "claude-sonnet-4-20250514",
    "anthropic.max_tokens": 1024,
    "schedule.interval": "rate(6 hours)",
}

ENV_OVERRIDES = {
    "ANTHROPIC_API_KEY": "anthropic.api_key",
    "EDGAR_CONTACT_EMAIL": "edgar.user_agent",
    "EMAIL_TO": "email.to",
    "EMAIL_FROM": "email.from",
    "S3_BUCKET_NAME": "s3.bucket_name",
}


def _get_nested(config: dict, dotted_key: str, default=None):
    """Get a value from a nested dict using a dotted key like 'email.to'."""
    keys = dotted_key.split(".")
    current = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _set_nested(config: dict, dotted_key: str, value):
    """Set a value in a nested dict using a dotted key like 'email.to'."""
    keys = dotted_key.split(".")
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def _validate_ticker(ticker: str) -> bool:
    """Validate that a ticker is a non-empty uppercase alphanumeric string."""
    return bool(ticker) and bool(re.match(r"^[A-Z0-9.-]+$", ticker.strip()))


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file, apply defaults and environment overrides."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"Config file {config_path} must contain a YAML mapping")

    # Apply defaults for missing values
    for dotted_key, default_value in DEFAULTS.items():
        if _get_nested(config, dotted_key) is None:
            _set_nested(config, dotted_key, default_value)

    # Apply environment variable overrides
    for env_var, dotted_key in ENV_OVERRIDES.items():
        env_value = os.environ.get(env_var)
        if env_value is not None:
            _set_nested(config, dotted_key, env_value)

    # Validate required fields
    for dotted_key, expected_type in REQUIRED_FIELDS.items():
        value = _get_nested(config, dotted_key)
        if value is None:
            raise ValueError(f"Missing required config field: {dotted_key}")
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Config field '{dotted_key}' must be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

    # Validate tickers
    tickers = config["tickers"]
    if not tickers:
        raise ValueError("Config field 'tickers' must not be empty")
    for ticker in tickers:
        if not isinstance(ticker, str) or not _validate_ticker(ticker):
            raise ValueError(
                f"Invalid ticker '{ticker}': must be non-empty uppercase alphanumeric"
            )

    return config
