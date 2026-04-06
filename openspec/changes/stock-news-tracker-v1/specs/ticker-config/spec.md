## ADDED Requirements

### Requirement: YAML configuration file
The system SHALL read configuration from a `config.yaml` file. The config MUST support: a list of tickers, schedule interval, email recipient, email sender, S3 bucket name, and EDGAR User-Agent details.

#### Scenario: Valid config loaded
- **WHEN** config.yaml contains tickers [AAPL, NVDA], schedule every 6h, and email to "user@example.com"
- **THEN** the system loads all values and uses them for the run

#### Scenario: Missing required fields
- **WHEN** config.yaml is missing the `tickers` field
- **THEN** the system exits with a clear error message indicating the missing field

### Requirement: Environment variable overrides
The system SHALL allow sensitive values (Anthropic API key, EDGAR contact email) to be provided via environment variables. Environment variables MUST take precedence over config.yaml values.

#### Scenario: API key from environment
- **WHEN** `ANTHROPIC_API_KEY` is set as an environment variable
- **THEN** the system uses that value regardless of any config.yaml setting

### Requirement: Config schema validation
The system SHALL validate the config against expected types and required fields at startup, before any API calls are made.

#### Scenario: Invalid ticker format
- **WHEN** a ticker value is an empty string or contains spaces
- **THEN** the system exits with a validation error before making any requests
