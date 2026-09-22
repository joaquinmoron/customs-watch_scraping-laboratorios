
COMPANIES = [
    {"name": "Eli Lilly and Company", "ticker": "LLY"},
    {"name": "Johnson & Johnson", "ticker": "JNJ"},
    {"name": "AbbVie Inc.", "ticker": "ABBV"},
    {"name": "Merck & Co., Inc.", "ticker": "MRK"},
    {"name": "Novartis AG", "ticker": "NVS"},
    {"name": "AstraZeneca PLC", "ticker": "AZN"},
    {"name": "Amgen Inc.", "ticker": "AMGN"},
    {"name": "Novo Nordisk A/S", "ticker": "NVO"},
    {"name": "Gilead Sciences, Inc.", "ticker": "GILD"},
    {"name": "Pfizer Inc.", "ticker": "PFE"},
]


import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone


class StockAnalysisScraper:
    def __init__(self, max_concurrency: int = 2):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = aiohttp.ClientTimeout(total=15)

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

    async def fetch_one(self, session: aiohttp.ClientSession, company: dict) -> dict | None:
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
                    "week_52_price_change": self._extraer_por_etiqueta(soup, "52-Week Price Change"),
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

def normalizar_precio(texto: str | None) -> float | None:
    if texto is None:
        return None

    texto = texto.strip()
    if texto in ("-", "", "N/A"):
        return None

    texto_limpio = texto.replace(",", "")
    return float(texto_limpio)

def normalizar_market_cap(texto: str | None) -> float | None:
    if texto is None:
        return None

    texto = texto.strip()
    if texto in ("-", "", "N/A"):
        return None

    texto = texto.replace("$", "").replace(",", "")

    multiplicadores = {"T": 1e12, "B": 1e9, "M": 1e6}
    ultima_letra = texto[-1]

    if ultima_letra in multiplicadores:
        numero = float(texto[:-1])
        return numero * multiplicadores[ultima_letra]

    return float(texto)

def normalizar_porcentaje(texto: str | None) -> float | None:
    if texto is None:
        return None

    texto = texto.strip()
    if texto in ("-", "", "N/A"):
        return None

    texto_limpio = texto.replace("%", "").replace("+", "").replace(",", "")
    return float(texto_limpio)

def normalizar_company(datos_crudos: dict) -> dict:
    return {
        "company_name": datos_crudos["company_name"],
        "ticker": datos_crudos["ticker"],
        "main_share_price": normalizar_precio(datos_crudos["main_share_price"]),
        "currency": datos_crudos["currency"],
        "market_cap": normalizar_market_cap(datos_crudos["market_cap"]),
        "week_52_price_change": normalizar_porcentaje(datos_crudos["week_52_price_change"]),
        "extracted_at_utc": datos_crudos["extracted_at_utc"],
    }

import sqlite3
import os

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            carpeta_actual = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(carpeta_actual, "laboratorios.db")
        self.db_path = db_path
        self._crear_tabla()

    def _crear_tabla(self):
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                main_share_price REAL,
                currency TEXT,
                market_cap REAL,
                week_52_price_change REAL,
                extracted_at_utc TEXT NOT NULL
            )
        """)
        conexion.commit()
        conexion.close()

    def guardar(self, company: dict):
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("""
            INSERT INTO companies (company_name, ticker, main_share_price, currency,
                                    market_cap, week_52_price_change, extracted_at_utc)
            VALUES (:company_name, :ticker, :main_share_price, :currency,
                    :market_cap, :week_52_price_change, :extracted_at_utc)
        """, company)
        conexion.commit()
        conexion.close()

async def main():
    scraper = StockAnalysisScraper(max_concurrency=2)
    resultados_crudos = await scraper.fetch_all(COMPANIES)
    
    resultados_normalizados = [normalizar_company(r) for r in resultados_crudos if r is not None]
    
    db = Database()
    for company in resultados_normalizados:
        db.guardar(company)
        print(f"Guardado: {company['ticker']}")

def ver_datos_guardados():
    db = Database()
    conexion = sqlite3.connect(db.db_path)
    cursor = conexion.execute("SELECT * FROM companies")
    for fila in cursor.fetchall():
        print(fila)
    conexion.close()

if __name__ == "__main__":
    asyncio.run(main())
    ver_datos_guardados()
    

