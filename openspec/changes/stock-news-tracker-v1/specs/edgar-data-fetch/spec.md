## ADDED Requirements

### Requirement: Fetch recent SEC filings for a ticker
The system SHALL query the SEC EDGAR full-text search API to retrieve recent filings (8-K, 10-Q, 10-K, Form 4) for a given stock ticker. The system MUST include a User-Agent header with a contact name and email as required by EDGAR's fair access policy.

#### Scenario: Successful filing retrieval
- **WHEN** the system requests filings for ticker "AAPL" with filing types ["8-K", "10-Q", "10-K", "4"]
- **THEN** the system returns a list of recent filings with accession number, filing type, filing date, and document URL for each

#### Scenario: No filings found for ticker
- **WHEN** the system requests filings for a ticker with no recent filings in the lookback window
- **THEN** the system returns an empty list without raising an error

### Requirement: Respect EDGAR rate limits
The system SHALL NOT exceed 10 requests per second to the SEC EDGAR API. The system MUST implement a delay between consecutive requests.

#### Scenario: Multiple tickers processed sequentially
- **WHEN** the system fetches filings for 5 tickers
- **THEN** each EDGAR API request is spaced at least 100ms apart

### Requirement: Extract filing content
The system SHALL download and extract the textual content from each filing document. For large filings (10-K, 10-Q), the system MUST extract only key sections (e.g., risk factors, financial highlights, management discussion) rather than the full document.

#### Scenario: 8-K filing content extraction
- **WHEN** the system processes an 8-K filing
- **THEN** the full filing text content is extracted and returned

#### Scenario: 10-K filing content extraction
- **WHEN** the system processes a 10-K filing
- **THEN** only key sections are extracted and the total text is truncated to a configurable maximum length

### Requirement: Configurable lookback window
The system SHALL support a configurable lookback period (in days) to control how far back to search for filings. The default lookback MUST be 7 days.

#### Scenario: Default lookback
- **WHEN** no lookback is specified in config
- **THEN** the system fetches filings from the last 7 days

#### Scenario: Custom lookback
- **WHEN** config specifies `lookback_days: 30`
- **THEN** the system fetches filings from the last 30 days
