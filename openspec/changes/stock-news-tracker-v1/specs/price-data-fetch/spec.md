## ADDED Requirements

### Requirement: Fetch current price data for a ticker
The system SHALL retrieve the current stock price data for a given ticker using yfinance. The data MUST include: current price, previous close, daily change (absolute and percentage), and volume.

#### Scenario: Successful price retrieval
- **WHEN** the system requests price data for ticker "NVDA"
- **THEN** the system returns a price snapshot containing current price, previous close, daily change, change percentage, and volume

#### Scenario: Invalid or delisted ticker
- **WHEN** the system requests price data for an unrecognized ticker
- **THEN** the system returns a null/empty result and logs a warning without crashing

### Requirement: Fetch recent price history
The system SHALL retrieve price history for a configurable period (default: 5 trading days) to provide trend context for LLM analysis.

#### Scenario: Default price history
- **WHEN** the system fetches price history with default settings
- **THEN** it returns the last 5 trading days of daily OHLCV data

#### Scenario: Custom history period
- **WHEN** config specifies `price_history_days: 30`
- **THEN** it returns the last 30 trading days of daily OHLCV data
