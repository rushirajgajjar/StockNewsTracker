## 1. Project Setup

- [x] 1.1 Initialize git repository and create .gitignore (Python, IDE, .env, __pycache__)
- [x] 1.2 Initialize Pipenv with Python 3.11 and install dependencies (anthropic, yfinance, boto3, pyyaml, jinja2, requests)
- [x] 1.3 Create project directory structure (src/, templates/, cdk/, tests/)
- [x] 1.4 Create config.yaml with example tickers, schedule, email, and EDGAR settings
- [x] 1.5 Create Dockerfile for Lambda container image

## 2. Configuration

- [x] 2.1 Implement config.py — YAML loader with schema validation and environment variable overrides
- [x] 2.2 Add validation for required fields (tickers, email.to, email.from) and ticker format

## 3. SEC EDGAR Data Fetch

- [x] 3.1 Implement edgar.py — EDGAR API client with User-Agent header and rate limiting (100ms between requests)
- [x] 3.2 Add filing search for configured types (8-K, 10-Q, 10-K, Form 4) with configurable lookback window
- [x] 3.3 Add filing content extraction — full text for 8-K, key sections only for 10-K/10-Q
- [x] 3.4 Handle edge cases: no filings found, EDGAR API errors, malformed filing content

## 4. Price Data Fetch

- [x] 4.1 Implement pricing.py — yfinance wrapper returning price snapshot (current, previous close, change, change %, volume)
- [x] 4.2 Add recent price history fetch (default 5 trading days of OHLCV data)
- [x] 4.3 Handle invalid/delisted tickers gracefully (return None, log warning)

## 5. LLM Analysis

- [x] 5.1 Implement analyzer.py — Claude API client that accepts filing content + price data per ticker
- [x] 5.2 Design prompt that requests structured output: summary, key points, sentiment (bullish/neutral/bearish), notable events
- [x] 5.3 Parse Claude response into structured data object
- [x] 5.4 Handle Claude API errors (timeout, rate limit) per ticker without failing the entire run

## 6. Email Report

- [x] 6.1 Create Jinja2 HTML email template (templates/email.html) with per-ticker sections, sentiment badges, and filing links
- [x] 6.2 Implement email_report.py — compose HTML from analysis results using Jinja2 template
- [x] 6.3 Add SES send function with configurable sender/recipient and subject "Stock Briefing - {date}"
- [x] 6.4 Handle SES errors (unverified email, send failure) with clear error logging

## 7. Data Archival

- [x] 7.1 Implement archiver.py — S3 upload for raw filing JSON (filings/{ticker}/{type}/{accession}.json)
- [x] 7.2 Add duplicate detection (skip if accession number already exists in S3)
- [x] 7.3 Add report archival (reports/{date}/briefing.html)

## 8. Lambda Handler

- [x] 8.1 Implement handler.py — Lambda entry point that orchestrates: load config → fetch filings → fetch prices → analyze → compose email → send → archive
- [x] 8.2 Add error handling and logging throughout the pipeline
- [x] 8.3 Add CloudWatch-friendly structured logging

## 9. CDK Infrastructure

- [x] 9.1 Initialize CDK app with Python (cdk/app.py, cdk/stack.py)
- [x] 9.2 Define Lambda function resource with Docker container image from ECR (512MB memory, 900s timeout)
- [x] 9.3 Define EventBridge rule with configurable schedule (default: every 6 hours)
- [x] 9.4 Define S3 bucket with IA lifecycle transition at 90 days
- [x] 9.5 Define SES email identity resources for sender/recipient
- [x] 9.6 Configure least-privilege IAM (SES SendEmail, S3 read/write, CloudWatch Logs)
- [x] 9.7 Wire environment variables (ANTHROPIC_API_KEY, config values) into Lambda

## 10. Testing and Validation

- [x] 10.1 Test config loading and validation with valid/invalid YAML
- [ ] 10.2 Test EDGAR client against live API with a known ticker
- [ ] 10.3 Test pricing module against yfinance with a known ticker
- [ ] 10.4 Test end-to-end locally: config → fetch → analyze → compose email (print to stdout instead of SES)
- [ ] 10.5 Build Docker image locally and verify Lambda handler invocation
- [ ] 10.6 Deploy CDK stack and trigger a test invocation
