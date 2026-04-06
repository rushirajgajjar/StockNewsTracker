"""Stock price data fetcher using yfinance."""

import logging
from dataclasses import dataclass

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class PriceSnapshot:
    ticker: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int


@dataclass
class PriceHistory:
    ticker: str
    dates: list[str]
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[int]


@dataclass
class PriceData:
    snapshot: PriceSnapshot | None
    history: PriceHistory | None


def get_price_snapshot(ticker: str) -> PriceSnapshot | None:
    """Get current price snapshot for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        previous_close = info.get("previousClose", 0)

        if not current_price:
            logger.warning(f"No price data available for {ticker}")
            return None

        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0

        return PriceSnapshot(
            ticker=ticker,
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=info.get("volume", 0) or 0,
        )
    except Exception as e:
        logger.warning(f"Failed to fetch price snapshot for {ticker}: {e}")
        return None


def get_price_history(ticker: str, days: int = 5) -> PriceHistory | None:
    """Get recent price history (OHLCV) for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        # Fetch extra days to account for weekends/holidays
        hist = stock.history(period=f"{days * 2}d")

        if hist.empty:
            logger.warning(f"No price history available for {ticker}")
            return None

        # Take only the requested number of trading days
        hist = hist.tail(days)

        return PriceHistory(
            ticker=ticker,
            dates=[d.strftime("%Y-%m-%d") for d in hist.index],
            open=[round(v, 2) for v in hist["Open"].tolist()],
            high=[round(v, 2) for v in hist["High"].tolist()],
            low=[round(v, 2) for v in hist["Low"].tolist()],
            close=[round(v, 2) for v in hist["Close"].tolist()],
            volume=[int(v) for v in hist["Volume"].tolist()],
        )
    except Exception as e:
        logger.warning(f"Failed to fetch price history for {ticker}: {e}")
        return None


def get_price_data(ticker: str, history_days: int = 5) -> PriceData:
    """Get both snapshot and history for a ticker."""
    return PriceData(
        snapshot=get_price_snapshot(ticker),
        history=get_price_history(ticker, days=history_days),
    )


def get_all_prices(tickers: list[str], history_days: int = 5) -> dict[str, PriceData]:
    """Get price data for all tickers."""
    results = {}
    for ticker in tickers:
        results[ticker] = get_price_data(ticker, history_days)
        logger.info(f"Fetched price data for {ticker}")
    return results
