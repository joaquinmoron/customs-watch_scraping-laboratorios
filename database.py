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