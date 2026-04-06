## Why

There is no automated, trustworthy way to get a periodic briefing on SEC filings and price movements for a personal stock watchlist. Existing tools are either paid, noisy with unreliable sources, or require manual checking. By pulling directly from SEC EDGAR (official, structured, free) and combining it with price data and LLM analysis, we can produce a concise, actionable email briefing on a configurable schedule — for essentially zero infrastructure cost.

## What Changes

- Introduce a Python Lambda function (Docker container) that:
  - Reads a YAML config of stock tickers
  - Fetches recent SEC EDGAR filings (8-K, 10-Q, 10-K, Form 4) per ticker
  - Fetches daily price snapshots via yfinance
  - Passes filings + price context to Claude API for analysis/summarization
  - Composes an HTML email report
  - Sends via AWS SES
  - Archives raw filing data to S3
- Introduce AWS CDK (Python) infrastructure stack for Lambda, EventBridge (cron), SES, S3, and ECR
- Introduce Pipenv-based dependency management and Docker container packaging

## Capabilities

### New Capabilities
- `edgar-data-fetch`: Fetch and parse SEC EDGAR filings (8-K, 10-Q, 10-K, Form 4) for configured tickers
- `price-data-fetch`: Retrieve daily stock price snapshots (price, volume, change %) via yfinance
- `llm-analysis`: Pass filing summaries and price data to Claude API for contextual analysis per ticker
- `email-report`: Compose and send HTML email briefing via AWS SES
- `data-archival`: Archive raw filing data to S3 for historical reference
- `ticker-config`: YAML-based configuration for tickers, schedule, and email settings
- `infra-cdk`: AWS CDK stack defining Lambda, EventBridge, SES, S3, and ECR resources

### Modified Capabilities
<!-- None — this is a greenfield project -->

## Impact

- **New dependencies**: anthropic SDK, yfinance, boto3, pyyaml, jinja2 (email templating)
- **AWS resources**: Lambda function, EventBridge rule, SES identity, S3 bucket, ECR repository
- **External APIs**: SEC EDGAR (rate limit: 10 req/sec, requires User-Agent header), Anthropic Claude API
- **Cost**: ~$1-5/month (almost entirely Claude API usage)
