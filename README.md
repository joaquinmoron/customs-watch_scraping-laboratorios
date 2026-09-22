# Scraping de Laboratorios Farmacéuticos

Prueba técnica — Python Developer Jr. Pipeline que extrae métricas financieras de las 10 principales
compañías farmacéuticas del mundo por capitalización bursátil, desde stockanalysis.com, y las persiste
en una base de datos SQLite.

## Estructura del proyecto

```
scraping_laboratorios/
├── cs_challenge_scrap.py   → versión completa, un solo archivo (lectura rápida)
├── main.py                  → punto de entrada de la versión organizada
├── companies.py               → lista de las 10 empresas
├── scraper.py                   → clase de extracción (scraping asíncrono)
├── normalizer.py                  → funciones de normalización de datos
├── database.py                      → clase de persistencia (SQLite)
├── test_normalizar.py                 → tests unitarios (pytest)
├── requirements.txt                     → dependencias del proyecto
└── README.md                              → este archivo
```

## Instalación

1. Clonar o descargar este repositorio.

2. Instalar las dependencias:

```bash
   pip install -r requirements.txt
```

## Ejecución

Para correr el pipeline completo (scraping → normalización → persistencia en SQLite):

```bash
python main.py
```

Esto va a:
1. Descargar los datos de las 10 empresas desde stockanalysis.com (de forma asíncrona, máximo 2 conexiones simultáneas).
2. Normalizar los valores extraídos (precios, market cap, cambio a 52 semanas) a tipos numéricos.
3. Guardar los resultados en `laboratorios.db` (SQLite), agregando una fila nueva por empresa en cada ejecución (se conserva el historial de corridas).

Para correr los tests unitarios:

```bash
pytest
```

> Nota: el archivo `cs_challenge_scrap.py` contiene la misma lógica completa en un único archivo,
> a modo de referencia para lectura rápida del pipeline de punta a punta. La versión organizada en
> módulos separados (`main.py`, `scraper.py`, `normalizer.py`, `database.py`, `companies.py`) es la
> versión final recomendada para mantenimiento y lectura del código.

## Criterio de selección de las empresas

Se seleccionaron las 10 principales compañías por capitalización bursátil dentro de la categoría
"Drug Manufacturers - General" de Stock Analysis
(`stockanalysis.com/stocks/industry/drug-manufacturers-general/`), consultado el 18/09/2026.

La fuente inicial de referencia para identificar candidatas fue companiesmarketcap.com
(`companiesmarketcap.com/pharmaceuticals/largest-pharmaceutical-companies-by-market-cap/`),
donde Roche (ROG / RHHBY) figura dentro del top 10 global de farmacéuticas. Sin embargo, Roche
no aparece dentro del ranking por market cap de la categoría equivalente en Stock Analysis (no
figura ni siquiera dentro del top 21 de esa categoría), por lo que se utilizó el ranking nativo
de Stock Analysis para mantener consistencia entre la fuente del criterio de selección y la
fuente de extracción de datos. Bajo ese ranking, la décima posición la ocupa Pfizer Inc. (PFE).

### Empresas incluidas

| Empresa | Ticker |
|---|---|
| Eli Lilly and Company | LLY |
| Johnson & Johnson | JNJ |
| AbbVie Inc. | ABBV |
| Merck & Co., Inc. | MRK |
| Novartis AG | NVS |
| AstraZeneca PLC | AZN |
| Amgen Inc. | AMGN |
| Novo Nordisk A/S | NVO |
| Gilead Sciences, Inc. | GILD |
| Pfizer Inc. | PFE |

## Tests unitarios

Se implementaron 3 tests unitarios sobre las funciones de normalización (`normalizer.py`),
que constituyen la lógica propia del proyecto — no requieren conexión HTTP ni acceso a una
base de datos real, ya que operan exclusivamente sobre strings en memoria.

Para correrlos:

```bash
pytest
```

| Test | Qué comprueba |
|---|---|
| `test_normalizar_market_cap_trillion` | Que la función reconoce correctamente el sufijo de magnitud "T" (trillion) y aplica el multiplicador correspondiente (×10¹²). Caso: `"1.03T"` → `1.03e12`. |
| `test_normalizar_porcentaje_dato_ausente` | Que un valor sin dato (representado como `"-"` en la web) se interpreta como `None`, y no genera un error ni se confunde con un valor numérico. |
| `test_normalizar_porcentaje_cero_real` | Que un valor de `"0.00%"` se interpreta como un cero real (`0.0`), diferenciándolo explícitamente de la ausencia de dato (`None`). Esta distinción es central en el diseño del pipeline: un dato faltante nunca se representa como cero. |

## Unidades de los datos guardados

| Campo | Unidad / formato |
|---|---|
| `main_share_price` | Número decimal, en la moneda indicada por `currency` (sin símbolo, sin separador de miles) |
| `market_cap` | Número decimal, expresado en unidades monetarias completas (ej. `1.03T` se guarda como `1030000000000.0`), no en millones ni billones abreviados |
| `week_52_price_change` | Número decimal que representa el porcentaje directamente (ej. `51.68` equivale a 51.68%, no a 0.5168) |
| `extracted_at_utc` | Fecha y hora en formato ISO 8601, huso horario UTC |

## Limitaciones conocidas

- **Dependencia de la estructura HTML de Stock Analysis.** El scraper utiliza selectores CSS
  específicos (por ejemplo, `div.text-4xl.font-bold` para el precio) basados en clases de
  utilidad de Tailwind CSS. Estas clases describen estilo visual, no significado semántico,
  por lo que un cambio de diseño en el sitio (sin cambio de contenido) podría romper el
  scraping sin previo aviso.

- **Los campos de tabla (Market Cap, 52-Week Price Change) se extraen buscando el texto de
  la etiqueta dentro de cualquier `<td>` de la página**, en lugar de por posición fija o clase
  CSS. Esta estrategia es más robusta ante reordenamientos de filas, pero depende de que el
  texto de la etiqueta (en inglés, tal como aparece en el sitio) se mantenga exactamente igual.

- **No se implementó reintento automático (retry) ante fallos de red.** Si una descarga falla
  (timeout, error HTTP, cambio de estructura), la empresa se omite de esa ejecución y se
  informa por consola, pero no se reintenta dentro de la misma corrida.

- **El pipeline no elimina datos históricos.** Cada ejecución agrega filas nuevas a la tabla
  `companies` sin sobrescribir corridas anteriores. Esto fue una decisión de diseño (para
  preservar el historial de extracciones), pero implica que la tabla crece indefinidamente
  con cada ejecución, sin un mecanismo de limpieza o archivado.

- **El campo `currency` se extrae parseando un string compuesto** (ej. `"NYSE: LLY · Real-Time
  Price · USD"`), asumiendo un formato de 3 partes separadas por "·". Si Stock Analysis
  cambiara ese formato (por ejemplo, agregando o quitando un segmento), la extracción de
  moneda podría devolver `None` o un valor incorrecto.

- **No se validó el comportamiento del scraper contra tickers de otras bolsas (ADRs no
  estadounidenses).** Todas las empresas seleccionadas cotizan en NYSE, por lo que no se
  probó si el formato de la página cambia para tickers de otras bolsas.

## Uso de IA

Se utilizó Claude (Anthropic) como asistente durante el desarrollo del proyecto, principalmente para:

- **Explicación de conceptos técnicos nuevos** (asincronía en Python, `Semaphore`,
  diferencias entre selectores CSS y búsqueda por texto en BeautifulSoup).
- **Diseño de la arquitectura del pipeline**, incluyendo la separación en módulos
  (`companies.py`, `scraper.py`, `normalizer.py`, `database.py`, `main.py`) y la decisión de
  diseño de conservar el historial de ejecuciones en la base en lugar de sobrescribir cada corrida.
- **Debugging guiado**, en particular la resolución de un caso real donde la función de
  extracción de campos por etiqueta (`_extraer_por_etiqueta`) fallaba silenciosamente porque
  el contenido de las celdas `<td>` estaba anidado dentro de un tag `<a>`, no como texto plano
  directo — se corrigió reemplazando `.string` por `.get_text()`.

### Cómo se validó lo generado

- Cada función de normalización se probó manualmente contra una tabla de casos de prueba
  definida antes de escribir el código (casos normales, datos ausentes, y el caso límite de
  "0.00%" vs. ausencia de dato), antes de formalizarla en los tests de `pytest`.
- El scraper se corrió repetidamente contra las 10 páginas reales de Stock Analysis, inspeccionando
  manualmente el HTML de cada selector propuesto (usando las herramientas de desarrollador del
  navegador) antes de incorporarlo al código, en lugar de asumir la estructura sin verificarla.
- Los resultados de cada corrida se revisaron campo por campo contra los valores visibles en el
  sitio web, para confirmar que la extracción y normalización devolvían los valores correctos.
- Se puede defender cada decisión de diseño del proyecto (por qué SQLite y no otro motor, por
  qué se conserva el historial, por qué se usa `get_text()` en lugar de `.string`, por qué el
  semáforo limita a 2 conexiones) con el razonamiento técnico correspondiente.

## Fuentes de consulta

Además del acompañamiento de Claude durante el desarrollo, se consultó el siguiente material
para reforzar la comprensión de conceptos de web scraping en Python:

- **"Scraping Data from a Real Website | Web Scraping in Python"** (YouTube) —
  [https://www.youtube.com/watch?v=8dTpNajxaH0](https://www.youtube.com/watch?v=8dTpNajxaH0)
  Usado para entender el flujo general de un scraper contra un sitio real: cómo identificar los
  datos a extraer en el HTML y estructurar el proceso de descarga y parseo.

- **"Web Scraping with AIOHTTP and Python"** (YouTube) —
  [https://www.youtube.com/watch?v=lUwZ9rS0SeM](https://www.youtube.com/watch?v=lUwZ9rS0SeM)
  Usado para reforzar el funcionamiento de `aiohttp` específicamente en un contexto de scraping
  (sesiones, requests asíncronas), complementando la documentación oficial.

- **Documentación oficial de aiohttp — Client Quickstart** —
  [https://docs.aiohttp.org/en/stable/client_quickstart.html](https://docs.aiohttp.org/en/stable/client_quickstart.html)
  Fuente de referencia primaria para el uso correcto de `ClientSession`, manejo de timeouts y
  el patrón `async with` en las requests HTTP del scraper.