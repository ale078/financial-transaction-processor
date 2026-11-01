"""Yahoo Finance CEDEAR market quote service with in-memory caching."""

import time
import json
import urllib.request
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Known CEDEAR tickers with their Yahoo Finance symbol and names
DEFAULT_CEDEAR_MAP = {
    "IBIT": {"symbol": "IBIT.BA", "name": "iShares Bitcoin Trust ETF", "underlying": "IBIT", "exchange": "BYMA"},
    "VIST": {"symbol": "VIST.BA", "name": "Vista Energy S.A.B.", "underlying": "VIST", "exchange": "BYMA"},
    "COIN": {"symbol": "COIN.BA", "name": "Coinbase Global Inc.", "underlying": "COIN", "exchange": "BYMA"},
    "ASML": {"symbol": "ASML.BA", "name": "ASML Holding N.V.", "underlying": "ASML", "exchange": "BYMA"},
    "GOOGL": {"symbol": "GOOGL.BA", "name": "Alphabet Inc. Cl A", "underlying": "GOOGL", "exchange": "BYMA"},
    "ETHA": {"symbol": "ETHA.BA", "name": "iShares Ethereum Trust ETF", "underlying": "ETHA", "exchange": "BYMA"},
    "HUT": {"symbol": "HUT.BA", "name": "Hut 8 Corp", "underlying": "HUT", "exchange": "BYMA"},
    "BITF": {"symbol": "BITF.BA", "name": "Bitfarms Ltd.", "underlying": "BITF", "exchange": "BYMA"},
    "OGZD": {"symbol": "OGZD.BA", "name": "Gazprom PAO ADR", "underlying": "OGZD", "exchange": "BYMA"},
    "AAPL": {"symbol": "AAPL.BA", "name": "Apple Inc.", "underlying": "AAPL", "exchange": "BYMA"},
    "MELI": {"symbol": "MELI.BA", "name": "MercadoLibre Inc.", "underlying": "MELI", "exchange": "BYMA"},
    "NVDA": {"symbol": "NVDA.BA", "name": "NVIDIA Corporation", "underlying": "NVDA", "exchange": "BYMA"},
    "TSLA": {"symbol": "TSLA.BA", "name": "Tesla Inc.", "underlying": "TSLA", "exchange": "BYMA"},
    "SPY": {"symbol": "SPY.BA", "name": "SPDR S&P 500 ETF Trust", "underlying": "SPY", "exchange": "BYMA"},
    "QQQ": {"symbol": "QQQ.BA", "name": "Invesco QQQ Trust", "underlying": "QQQ", "exchange": "BYMA"},
}

class CedearPriceService:
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_fetched: float = 0

    def fetch_single(self, yahoo_symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quotes from Yahoo Finance v8 chart API for a single ticker."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=1d&interval=1d"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
                result = data.get("chart", {}).get("result")
                if not result:
                    return None
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
                change = (price - prev_close) if (price is not None and prev_close is not None) else 0.0
                change_pct = ((change / prev_close) * 100) if prev_close else 0.0

                return {
                    "symbol": yahoo_symbol,
                    "price": price,
                    "previous_close": prev_close,
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "currency": meta.get("currency", "ARS"),
                    "updated_at": meta.get("regularMarketTime"),
                    "status": "ok"
                }
        except Exception as e:
            logger.warning(f"Failed fetching {yahoo_symbol} from Yahoo Finance: {e}")
            return {
                "symbol": yahoo_symbol,
                "error": str(e),
                "status": "error"
            }

    def get_quotes(self, tickers: Optional[List[str]] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch quotes for a list of tickers (e.g. ['IBIT', 'VIST', 'COIN'])."""
        now = time.time()
        target_tickers = [t.upper().strip() for t in (tickers or list(DEFAULT_CEDEAR_MAP.keys()))]

        # Check cache if not forced
        if not force_refresh and (now - self._last_fetched < self.cache_ttl) and self._cache:
            # Check if all targets are present in cache
            if all(t in self._cache for t in target_tickers):
                return {
                    "quotes": {t: self._cache[t] for t in target_tickers if t in self._cache},
                    "cached": True,
                    "cached_since_seconds": round(now - self._last_fetched)
                }

        results = {}
        for ticker in target_tickers:
            meta = DEFAULT_CEDEAR_MAP.get(ticker, {
                "symbol": f"{ticker}.BA",
                "name": f"CEDEAR {ticker}",
                "underlying": ticker,
                "exchange": "BYMA"
            })
            symbol = meta["symbol"]
            
            quote = self.fetch_single(symbol)
            if not quote or quote.get("status") == "error":
                # Try fallback without .BA if foreign
                fallback_quote = self.fetch_single(ticker)
                if fallback_quote and fallback_quote.get("status") == "ok":
                    quote = fallback_quote
                    quote["note"] = "Cotización de subyacente en USD"

            if quote and quote.get("status") == "ok":
                combined = {
                    "ticker": ticker,
                    "name": meta.get("name", ticker),
                    "symbol": symbol,
                    "exchange": meta.get("exchange", "BYMA"),
                    **quote
                }
            else:
                combined = {
                    "ticker": ticker,
                    "name": meta.get("name", ticker),
                    "symbol": symbol,
                    "exchange": meta.get("exchange", "BYMA"),
                    "price": None,
                    "previous_close": None,
                    "change": 0.0,
                    "change_pct": 0.0,
                    "currency": "ARS",
                    "status": "unavailable",
                    "error": quote.get("error") if quote else "No data"
                }

            results[ticker] = combined
            self._cache[ticker] = combined

        self._last_fetched = now
        return {
            "quotes": results,
            "cached": False,
            "cached_since_seconds": 0
        }
