import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from companies import COMPANIES


class StockAnalysisScraper:
    def __init__(self, max_concurrency: int = 2):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = aiohttp.ClientTimeout(total=15)

    async def fetch_one(
        self, session: aiohttp.ClientSession, company: dict
    ) -> dict | None:
        ticker = company["ticker"]
        url = f"https://stockanalysis.com/stocks/{ticker}/statistics/"

        async with self._semaphore:
            try:
                async with session.get(url, timeout=self._timeout) as response:
                    response.raise_for_status()
                    html = await response.text()

                soup = BeautifulSoup(html, "lxml")

                return {
                    "company_name": company["name"],
                    "ticker": ticker,
                    "main_share_price": self._extraer_precio(soup),
                    "currency": self._extraer_moneda(soup),
                    "market_cap": self._extraer_por_etiqueta(soup, "Market Cap"),
                    "week_52_price_change": self._extraer_por_etiqueta(
                        soup, "52-Week Price Change"
                    ),
                    "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                print(f"[ERROR] {ticker}: {e}")
                return None

    async def fetch_all(self, companies: list[dict]) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_one(session, company) for company in companies]
            resultados = await asyncio.gather(*tasks)
        return resultados

    def _extraer_precio(self, soup: BeautifulSoup) -> str | None:
        elemento = soup.select_one("div.text-4xl.font-bold")
        return elemento.text.strip() if elemento else None

    def _extraer_moneda(self, soup: BeautifulSoup) -> str | None:
        elemento = soup.select_one("div.text-tiny.text-faded")
        if elemento is None:
            return None
        partes = elemento.text.strip().split("·")
        if len(partes) < 3:
            return None
        return partes[-1].strip()

    def _extraer_por_etiqueta(self, soup: BeautifulSoup, etiqueta: str) -> str | None:
        for td in soup.find_all("td"):
            if etiqueta in td.get_text():
                valor_td = td.find_next_sibling("td")
                if valor_td:
                    return valor_td.get_text(strip=True)
        return None

    
