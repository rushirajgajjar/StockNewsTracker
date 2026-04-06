## ADDED Requirements

### Requirement: Analyze filings with price context
The system SHALL pass filing summaries and price data for each ticker to the Claude API and return a structured analysis. The prompt MUST include: filing content, filing type and date, current price data, and recent price history.

#### Scenario: Ticker with new filings
- **WHEN** the system has 2 recent 8-K filings and price data for "AAPL"
- **THEN** Claude API is called with the filing content and price context, and returns an analysis covering: key takeaways from filings, potential market impact, and overall sentiment (bullish/neutral/bearish)

#### Scenario: Ticker with no new filings
- **WHEN** the system has no recent filings but has price data for "TSLA"
- **THEN** Claude API is called with price data only, and returns a brief price movement summary without filing analysis

### Requirement: Structured analysis output
The system SHALL request Claude to return analysis in a consistent structure containing: a summary (2-3 sentences), key points (bullet list), sentiment label (bullish/neutral/bearish), and notable events (if any).

#### Scenario: Analysis response parsing
- **WHEN** Claude returns an analysis for a ticker
- **THEN** the system extracts summary, key points, sentiment, and notable events into a structured data object

### Requirement: Handle API errors gracefully
The system SHALL handle Claude API errors (rate limits, timeouts, server errors) without failing the entire run. If analysis fails for one ticker, the system MUST continue processing remaining tickers.

#### Scenario: Claude API timeout for one ticker
- **WHEN** the Claude API call times out for "AAPL" but succeeds for "NVDA"
- **THEN** the report includes the NVDA analysis and marks AAPL as "analysis unavailable"
