from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

ENDPOINTS = {
    "profile": "/profile/{ticker}",
    "quote": "/quote/{ticker}",
    "income_statement": "/income-statement/{ticker}?period=quarter&limit=8",
    "balance_sheet": "/balance-sheet-statement/{ticker}?period=quarter&limit=8",
    "cash_flow": "/cash-flow-statement/{ticker}?period=quarter&limit=8",
    "analyst_estimates": "/analyst-estimates/{ticker}?period=quarter&limit=8",
    "price_target": "/price-target-consensus/{ticker}",
    "historical": "/historical-price-full/{ticker}?from=2026-03-01&to=2026-04-30",
}


class FMPClient:
    def __init__(self, api_key: str | None, cache_dir: Path) -> None:
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_endpoint(self, ticker: str, endpoint_name: str, *, refresh: bool = False) -> dict[str, Any] | list[Any]:
        if endpoint_name not in ENDPOINTS:
            raise ValueError(f"unknown FMP endpoint: {endpoint_name}")
        cache_path = self.cache_dir / f"fmp_{ticker.replace('/', '_')}_{endpoint_name}.json"
        if cache_path.exists() and not refresh:
            return json.loads(cache_path.read_text())
        if not self.api_key:
            return {"ticker": ticker, "endpoint": endpoint_name, "status": "skipped_missing_fmp_key"}

        endpoint = ENDPOINTS[endpoint_name].format(ticker=urllib.parse.quote(ticker))
        separator = "&" if "?" in endpoint else "?"
        url = f"{FMP_BASE_URL}{endpoint}{separator}apikey={urllib.parse.quote(self.api_key)}"
        request = urllib.request.Request(url, headers={"User-Agent": "stack-hbm-swarm/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            payload = {"ticker": ticker, "endpoint": endpoint_name, "status": "error", "error": str(exc)}
        cache_path.write_text(json.dumps(payload, indent=2))
        return payload

    def fetch_bundle(self, tickers: list[str], *, refresh: bool = False) -> dict[str, dict[str, Any] | list[Any]]:
        results: dict[str, dict[str, Any] | list[Any]] = {}
        for ticker in tickers:
            for endpoint_name in ENDPOINTS:
                key = f"{ticker}:{endpoint_name}"
                results[key] = self.fetch_endpoint(ticker, endpoint_name, refresh=refresh)
        return results

