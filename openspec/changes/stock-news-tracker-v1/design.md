## Context

This is a greenfield personal project. No existing codebase — empty repository. The user has experience with AWS (Lambda, S3, SES) from a prior Finance project that uses SAM + Pipenv. This project follows similar patterns but uses CDK instead of SAM, and Docker containers instead of ZIP packaging due to heavier dependencies.

The system pulls from two external data sources (SEC EDGAR API, Yahoo Finance via yfinance), processes data through Claude API, and delivers results via email. All components run within a single Lambda invocation triggered on a schedule.

## Goals / Non-Goals

**Goals:**
- Automated, periodic stock briefing emails from official SEC filing data
- Clean separation of concerns: data fetching, analysis, delivery
- Infrastructure-as-code via CDK for reproducible deployments
- Minimal cost (~$1-5/month) for personal use
- Simple YAML-based configuration for tickers and settings

**Non-Goals:**
- Real-time data or streaming (periodic batch is sufficient)
- Local CLI mode or ChromaDB integration (deferred to v2)
- Multi-user support or authentication
- Web UI or dashboard
- Support for non-SEC news sources in v1
- High-frequency trading signals or financial advice

## Decisions

### 1. Lambda with Docker container (not ZIP)

**Choice**: Package Lambda as a Docker container image pushed to ECR.

**Why**: The dependency set (yfinance, anthropic SDK, boto3, pyyaml, jinja2) exceeds comfortable ZIP packaging limits. Container images support up to 10GB and give full control over the runtime environment.

**Alternatives considered**:
- ZIP deployment (like the Finance project): Too tight on the 250MB limit with yfinance + transitive deps
- Lambda Layers: Fragile dependency management, version pinning issues
- ECS Fargate: Overkill for a periodic batch job that runs in < 5 minutes

### 2. AWS CDK over SAM/Terraform

**Choice**: AWS CDK with Python.

**Why**: More configurable than SAM, same language as the application (Python), and better abstractions for multi-resource stacks. The user explicitly chose this over SAM.

**Alternatives considered**:
- SAM (used in Finance project): Less flexible for complex resource relationships
- Terraform: Different language (HCL), heavier tooling for a single-stack project

### 3. SEC EDGAR as sole news source

**Choice**: Only use SEC EDGAR filings for v1.

**Why**: Official, structured, free, no scraping required. Filings are legally mandated disclosures — the most trustworthy source possible. 8-K filings serve as the "news" feed (material events within 4 business days).

**Alternatives considered**:
- RSS feeds from news outlets: Variable quality, scraping concerns
- NewsAPI: Paid for production use, less authoritative
- Multiple sources: Increases complexity without proportional v1 value

### 4. Single Lambda, sequential processing

**Choice**: One Lambda function processes all tickers sequentially per invocation.

**Why**: For ~5 tickers, total execution time is well under Lambda's 15-minute limit. Simplicity outweighs parallelism at this scale.

**Alternatives considered**:
- Fan-out with Step Functions: Unnecessary complexity for < 10 tickers
- One Lambda per ticker: More infra to manage, coordination overhead

### 5. S3 for raw data archival

**Choice**: Store raw filing data in S3, organized by ticker and date.

**Why**: Cheap, durable storage. Enables future v2 features (ChromaDB indexing, historical analysis) without re-fetching from EDGAR.

**S3 key structure**:
```
s3://stocknewstracker-archive/
  └── filings/
      └── {ticker}/
          └── {filing_type}/
              └── {accession_number}.json
  └── reports/
      └── {date}/
          └── briefing.html
```

### 6. Project structure

```
StockNewsTracker/
├── Pipfile / Pipfile.lock
├── Dockerfile
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── handler.py          # Lambda entry point
│   ├── edgar.py             # SEC EDGAR API client
│   ├── pricing.py           # yfinance price fetcher
│   ├── analyzer.py          # Claude API analysis
│   ├── email_report.py      # HTML composition + SES send
│   ├── archiver.py          # S3 archival
│   └── config.py            # YAML config loader
├── templates/
│   └── email.html           # Jinja2 email template
├── cdk/
│   ├── app.py               # CDK app entry point
│   └── stack.py             # CDK stack definition
└── tests/
    └── ...
```

## Risks / Trade-offs

**[SEC EDGAR rate limit: 10 req/sec]** → Implement simple rate limiting with sleep intervals between requests. At ~5 tickers with 4 filing types each, this is ~20 requests — well within limits even at 1 req/sec.

**[yfinance is unofficial and could break]** → It's widely used and actively maintained. If it breaks, swapping to another free price API (e.g., Alpha Vantage free tier) is isolated to `pricing.py`.

**[Claude API cost scales with filing size]** → Summarize/truncate large filings before sending to Claude. 10-K annual reports can be massive — extract key sections (risk factors, financial highlights) rather than sending the full document.

**[Lambda cold start with Docker container]** → Cold starts can be 5-10 seconds for container images. Acceptable for a scheduled batch job — not user-facing latency.

**[SES requires verified email/domain]** → Must verify sender and recipient email in SES sandbox mode, or request production access. Document this in setup instructions.

**[EDGAR filing format varies]** → 8-K filings are relatively consistent, but older filings may use different HTML structures. Focus on recent filings (configurable lookback window) to minimize parsing edge cases.
