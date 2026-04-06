"""S3 archival for raw filing data and generated reports."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .edgar import Filing

logger = logging.getLogger(__name__)


@dataclass
class Archiver:
    bucket_name: str
    _s3: object = None

    def __post_init__(self):
        self._s3 = boto3.client("s3")

    def _key_exists(self, key: str) -> bool:
        """Check if an S3 key already exists."""
        try:
            self._s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def archive_filing(self, filing: Filing) -> bool:
        """Archive a single filing to S3. Skips if already exists."""
        key = (
            f"filings/{filing.ticker}/{filing.filing_type}/"
            f"{filing.accession_number}.json"
        )

        if self._key_exists(key):
            logger.info(f"Filing already archived: {key}")
            return False

        data = {
            "ticker": filing.ticker,
            "filing_type": filing.filing_type,
            "accession_number": filing.accession_number,
            "filing_date": filing.filing_date,
            "document_url": filing.document_url,
            "description": filing.description,
            "content": filing.content,
            "archived_at": datetime.now().isoformat(),
        }

        self._s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )
        logger.info(f"Archived filing: {key}")
        return True

    def archive_filings(self, filings_by_ticker: dict[str, list[Filing]]) -> int:
        """Archive all filings. Returns count of newly archived files."""
        count = 0
        for filings in filings_by_ticker.values():
            for filing in filings:
                if self.archive_filing(filing):
                    count += 1
        return count

    def archive_report(self, html_content: str, date: str | None = None) -> str:
        """Archive the generated HTML report to S3."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        key = f"reports/{date}/briefing.html"

        self._s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=html_content,
            ContentType="text/html",
        )
        logger.info(f"Archived report: {key}")
        return key
