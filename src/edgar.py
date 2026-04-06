"""SEC EDGAR API client for fetching and parsing company filings."""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_FILING_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
EDGAR_FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

REQUEST_INTERVAL = 0.15  # 150ms between requests (well under 10 req/sec)


@dataclass
class Filing:
    ticker: str
    filing_type: str
    accession_number: str
    filing_date: str
    document_url: str
    description: str = ""
    content: str = ""


@dataclass
class EdgarClient:
    user_agent: str
    filing_types: list = field(default_factory=lambda: ["8-K", "10-Q", "10-K", "4"])
    lookback_days: int = 7
    max_content_length: int = 50000
    _last_request_time: float = field(default=0.0, repr=False)
    _ticker_to_cik: dict = field(default_factory=dict, repr=False)

    def _rate_limit(self):
        """Enforce rate limiting between EDGAR requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str) -> requests.Response:
        """Make a rate-limited GET request to EDGAR."""
        self._rate_limit()
        headers = {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response

    def _load_cik_mapping(self):
        """Load the ticker-to-CIK mapping from SEC."""
        if self._ticker_to_cik:
            return
        try:
            response = self._get(EDGAR_COMPANY_TICKERS_URL)
            data = response.json()
            for entry in data.values():
                ticker = entry.get("ticker", "").upper()
                cik = str(entry.get("cik_str", ""))
                if ticker and cik:
                    self._ticker_to_cik[ticker] = cik.zfill(10)
        except Exception as e:
            logger.error(f"Failed to load CIK mapping: {e}")

    def _get_cik(self, ticker: str) -> str | None:
        """Get CIK number for a ticker."""
        self._load_cik_mapping()
        return self._ticker_to_cik.get(ticker.upper())

    def get_filings(self, ticker: str) -> list[Filing]:
        """Fetch recent filings for a ticker from EDGAR."""
        cik = self._get_cik(ticker)
        if not cik:
            logger.warning(f"No CIK found for ticker {ticker}")
            return []

        try:
            url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
            response = self._get(url)
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"EDGAR API error for {ticker}: {e}")
            return []

        filings = []
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        recent_filings = data.get("filings", {}).get("recent", {})

        forms = recent_filings.get("form", [])
        dates = recent_filings.get("filingDate", [])
        accessions = recent_filings.get("accessionNumber", [])
        primary_docs = recent_filings.get("primaryDocument", [])
        descriptions = recent_filings.get("primaryDocDescription", [])

        for i in range(len(forms)):
            form = forms[i]
            # Match filing types (Form 4 is just "4" in EDGAR)
            if form not in self.filing_types:
                continue

            filing_date_str = dates[i]
            try:
                filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            except ValueError:
                continue

            if filing_date < cutoff_date:
                continue

            accession = accessions[i]
            accession_no_dashes = accession.replace("-", "")
            primary_doc = primary_docs[i]
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik.lstrip('0')}/{accession_no_dashes}/{primary_doc}"
            )

            filing = Filing(
                ticker=ticker,
                filing_type=form,
                accession_number=accession,
                filing_date=filing_date_str,
                document_url=doc_url,
                description=descriptions[i] if i < len(descriptions) else "",
            )
            filings.append(filing)

        logger.info(f"Found {len(filings)} filings for {ticker}")
        return filings

    def fetch_filing_content(self, filing: Filing) -> str:
        """Download and extract text content from a filing."""
        try:
            response = self._get(filing.document_url)
            content = response.text
        except requests.RequestException as e:
            logger.error(
                f"Failed to fetch filing content for {filing.ticker} "
                f"({filing.accession_number}): {e}"
            )
            return ""

        # Strip HTML tags for a rough text extraction
        text = re.sub(r"<[^>]+>", " ", content)
        text = re.sub(r"\s+", " ", text).strip()

        # For large filings (10-K, 10-Q), extract key sections and truncate
        if filing.filing_type in ("10-K", "10-Q"):
            text = self._extract_key_sections(text)

        if len(text) > self.max_content_length:
            text = text[: self.max_content_length] + "\n[TRUNCATED]"

        return text

    def _extract_key_sections(self, text: str) -> str:
        """Extract key sections from large filings (10-K, 10-Q)."""
        key_headers = [
            "risk factors",
            "management's discussion and analysis",
            "financial highlights",
            "results of operations",
            "financial condition",
            "liquidity and capital resources",
        ]
        sections = []
        text_lower = text.lower()

        for header in key_headers:
            idx = text_lower.find(header)
            if idx != -1:
                # Extract ~5000 chars after the header
                section = text[idx : idx + 5000]
                sections.append(section)

        if sections:
            return "\n\n---\n\n".join(sections)
        # If no key sections found, return the beginning of the document
        return text[: self.max_content_length]

    def fetch_all(self, tickers: list[str]) -> dict[str, list[Filing]]:
        """Fetch filings for all tickers, with content populated."""
        results = {}
        for ticker in tickers:
            filings = self.get_filings(ticker)
            for filing in filings:
                filing.content = self.fetch_filing_content(filing)
            results[ticker] = filings
        return results
