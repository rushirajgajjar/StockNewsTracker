## ADDED Requirements

### Requirement: Compose HTML email report
The system SHALL compose an HTML email using a Jinja2 template. The email MUST contain: a date header, a section per ticker with its analysis, price data summary, and filing references.

#### Scenario: Report with multiple tickers
- **WHEN** analyses for 3 tickers are available
- **THEN** the email contains a section for each ticker with summary, key points, sentiment badge, price snapshot, and links to original filings on EDGAR

#### Scenario: Report with mixed results
- **WHEN** analysis succeeded for 2 tickers and failed for 1
- **THEN** the email includes full sections for successful tickers and a notice for the failed one

### Requirement: Send email via AWS SES
The system SHALL send the composed HTML email via AWS SES to the recipient configured in config.yaml. The sender address MUST also be configurable.

#### Scenario: Successful email delivery
- **WHEN** the report is composed and SES credentials are valid
- **THEN** the email is sent with subject "Stock Briefing - {date}" to the configured recipient

#### Scenario: SES send failure
- **WHEN** SES returns an error (e.g., unverified email)
- **THEN** the system logs the error with the SES error message and exits with a non-zero status

### Requirement: Email subject includes date
The system SHALL format the email subject as "Stock Briefing - {YYYY-MM-DD}" using the current date.

#### Scenario: Email subject format
- **WHEN** the report is generated on 2026-04-05
- **THEN** the email subject is "Stock Briefing - 2026-04-05"
