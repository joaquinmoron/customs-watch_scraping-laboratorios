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