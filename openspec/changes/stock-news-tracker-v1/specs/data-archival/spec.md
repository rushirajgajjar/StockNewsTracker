## ADDED Requirements

### Requirement: Archive raw filing data to S3
The system SHALL store raw filing data in S3 after each run. Files MUST be organized as `filings/{ticker}/{filing_type}/{accession_number}.json`.

#### Scenario: Successful archival
- **WHEN** the system fetches 3 filings for ticker "AAPL"
- **THEN** 3 JSON files are written to S3 under `filings/AAPL/{filing_type}/` with the filing content and metadata

#### Scenario: Duplicate filing already archived
- **WHEN** a filing with the same accession number already exists in S3
- **THEN** the system skips uploading the duplicate

### Requirement: Archive generated report
The system SHALL store each generated HTML email report in S3 under `reports/{date}/briefing.html`.

#### Scenario: Report archival
- **WHEN** a briefing is generated on 2026-04-05
- **THEN** the HTML report is stored at `reports/2026-04-05/briefing.html` in S3
