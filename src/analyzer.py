"""Claude API client for analyzing SEC filings with price context."""

import json
import logging
from dataclasses import dataclass, field

import anthropic

from .edgar import Filing
from .pricing import PriceData

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """\
You are a financial analyst assistant. Analyze the following SEC filing(s) and stock \
price data for {ticker}. Provide a concise, structured analysis.

{filings_section}

{price_section}

Respond in the following JSON format (and nothing else):
{{
  "summary": "2-3 sentence overview of the key findings",
  "key_points": ["point 1", "point 2", "point 3"],
  "sentiment": "bullish" | "neutral" | "bearish",
  "notable_events": ["event 1", "event 2"] or []
}}

Focus on material information that could affect the stock price. Be specific and \
actionable. If there are no filings, focus on price movement analysis only.
"""


@dataclass
class TickerAnalysis:
    ticker: str
    summary: str
    key_points: list[str]
    sentiment: str  # "bullish", "neutral", "bearish"
    notable_events: list[str]
    error: str | None = None


@dataclass
class Analyzer:
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    _client: anthropic.Anthropic | None = field(default=None, repr=False)

    def __post_init__(self):
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def _build_filings_section(self, filings: list[Filing]) -> str:
        if not filings:
            return "No recent SEC filings found for this ticker."

        sections = []
        for f in filings:
            content_preview = f.content[:3000] if f.content else "Content unavailable"
            sections.append(
                f"### {f.filing_type} — Filed {f.filing_date}\n"
                f"Accession: {f.accession_number}\n"
                f"URL: {f.document_url}\n\n"
                f"{content_preview}"
            )
        return "## SEC Filings\n\n" + "\n\n---\n\n".join(sections)

    def _build_price_section(self, price_data: PriceData | None) -> str:
        if not price_data or not price_data.snapshot:
            return "No price data available."

        s = price_data.snapshot
        lines = [
            "## Price Data",
            f"Current: ${s.current_price} | Previous Close: ${s.previous_close}",
            f"Change: ${s.change} ({s.change_percent}%) | Volume: {s.volume:,}",
        ]

        if price_data.history:
            h = price_data.history
            lines.append("\nRecent History:")
            for i in range(len(h.dates)):
                lines.append(
                    f"  {h.dates[i]}: O={h.open[i]} H={h.high[i]} "
                    f"L={h.low[i]} C={h.close[i]} V={h.volume[i]:,}"
                )

        return "\n".join(lines)

    def analyze_ticker(
        self,
        ticker: str,
        filings: list[Filing],
        price_data: PriceData | None,
    ) -> TickerAnalysis:
        """Analyze filings and price data for a single ticker using Claude."""
        prompt = ANALYSIS_PROMPT.format(
            ticker=ticker,
            filings_section=self._build_filings_section(filings),
            price_section=self._build_price_section(price_data),
        )

        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            analysis = json.loads(response_text)

            return TickerAnalysis(
                ticker=ticker,
                summary=analysis.get("summary", ""),
                key_points=analysis.get("key_points", []),
                sentiment=analysis.get("sentiment", "neutral"),
                notable_events=analysis.get("notable_events", []),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response for {ticker}: {e}")
            return TickerAnalysis(
                ticker=ticker,
                summary="",
                key_points=[],
                sentiment="neutral",
                notable_events=[],
                error=f"Failed to parse analysis response: {e}",
            )
        except anthropic.APIError as e:
            logger.error(f"Claude API error for {ticker}: {e}")
            return TickerAnalysis(
                ticker=ticker,
                summary="",
                key_points=[],
                sentiment="neutral",
                notable_events=[],
                error=f"Analysis unavailable: {e}",
            )

    def analyze_all(
        self,
        filings_by_ticker: dict[str, list[Filing]],
        prices_by_ticker: dict[str, PriceData],
    ) -> dict[str, TickerAnalysis]:
        """Analyze all tickers."""
        results = {}
        for ticker in filings_by_ticker:
            filings = filings_by_ticker.get(ticker, [])
            price_data = prices_by_ticker.get(ticker)
            results[ticker] = self.analyze_ticker(ticker, filings, price_data)
            logger.info(
                f"Analysis complete for {ticker}: {results[ticker].sentiment}"
            )
        return results
