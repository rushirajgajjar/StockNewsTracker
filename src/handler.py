"""Lambda entry point that orchestrates the full pipeline."""

import json
import logging
import sys
from datetime import datetime

from .analyzer import Analyzer
from .archiver import Archiver
from .config import load_config
from .edgar import EdgarClient
from .email_report import compose_report, send_email
from .pricing import get_all_prices

# CloudWatch-friendly structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            json.dumps(
                {
                    "timestamp": "%(asctime)s",
                    "level": "%(levelname)s",
                    "module": "%(module)s",
                    "message": "%(message)s",
                }
            )
        )
    )
    logger.addHandler(handler)


def lambda_handler(event=None, context=None):
    """Main Lambda handler: config -> fetch -> analyze -> email -> archive."""
    run_start = datetime.now()
    logger.info(f"StockNewsTracker run started at {run_start.isoformat()}")

    # 1. Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Config loading failed: {e}")
        return {"statusCode": 500, "body": f"Config error: {e}"}

    tickers = config["tickers"]
    logger.info(f"Processing {len(tickers)} tickers: {', '.join(tickers)}")

    # 2. Fetch SEC filings
    logger.info("Fetching SEC EDGAR filings...")
    edgar_config = config.get("edgar", {})
    edgar_client = EdgarClient(
        user_agent=edgar_config.get("user_agent", ""),
        filing_types=edgar_config.get("filing_types", ["8-K", "10-Q", "10-K", "4"]),
        lookback_days=edgar_config.get("lookback_days", 7),
        max_content_length=edgar_config.get("max_content_length", 50000),
    )
    filings_by_ticker = edgar_client.fetch_all(tickers)

    total_filings = sum(len(f) for f in filings_by_ticker.values())
    logger.info(f"Found {total_filings} filings across {len(tickers)} tickers")

    # 3. Fetch price data
    logger.info("Fetching price data...")
    pricing_config = config.get("pricing", {})
    prices_by_ticker = get_all_prices(
        tickers, history_days=pricing_config.get("history_days", 5)
    )

    # 4. Analyze with Claude
    logger.info("Running LLM analysis...")
    anthropic_config = config.get("anthropic", {})
    api_key = anthropic_config.get("api_key", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not configured")
        return {"statusCode": 500, "body": "Missing ANTHROPIC_API_KEY"}

    analyzer = Analyzer(
        api_key=api_key,
        model=anthropic_config.get("model", "claude-sonnet-4-20250514"),
        max_tokens=anthropic_config.get("max_tokens", 1024),
    )
    analyses = analyzer.analyze_all(filings_by_ticker, prices_by_ticker)

    # 5. Compose and send email
    logger.info("Composing email report...")
    html_report = compose_report(analyses, prices_by_ticker, filings_by_ticker)

    email_config = config.get("email", {})
    try:
        send_email(
            html_body=html_report,
            to_address=email_config["to"],
            from_address=email_config["from"],
        )
    except Exception as e:
        logger.error(f"Email delivery failed: {e}")
        # Continue to archival even if email fails

    # 6. Archive data
    logger.info("Archiving data to S3...")
    s3_config = config.get("s3", {})
    bucket_name = s3_config.get("bucket_name")
    if bucket_name:
        archiver = Archiver(bucket_name=bucket_name)
        archived_count = archiver.archive_filings(filings_by_ticker)
        archiver.archive_report(html_report)
        logger.info(f"Archived {archived_count} new filings and report")
    else:
        logger.warning("S3 bucket not configured, skipping archival")

    elapsed = (datetime.now() - run_start).total_seconds()
    logger.info(f"Run completed in {elapsed:.1f}s")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "tickers_processed": len(tickers),
                "filings_found": total_filings,
                "elapsed_seconds": elapsed,
            }
        ),
    }
