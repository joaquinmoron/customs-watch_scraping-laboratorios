import asyncio

from companies import COMPANIES
from scraper import StockAnalysisScraper
from normalizer import normalizar_company
from database import Database


async def main():
    scraper = StockAnalysisScraper(max_concurrency=2)
    resultados_crudos = await scraper.fetch_all(COMPANIES)

    resultados_normalizados = [normalizar_company(r) for r in resultados_crudos if r is not None]

    db = Database()
    for company in resultados_normalizados:
        db.guardar(company)
        print(f"Guardado: {company['ticker']}")


if __name__ == "__main__":
    asyncio.run(main())
    