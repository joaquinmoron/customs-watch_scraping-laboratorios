from cs_challenge_scrap import normalizar_market_cap, normalizar_porcentaje


def test_normalizar_market_cap_trillion():
    """Comprueba que reconoce la magnitud 'T' y multiplica correctamente por 1e12."""
    resultado = normalizar_market_cap("1.03T")
    assert resultado == 1.03e12


def test_normalizar_porcentaje_dato_ausente():
    """Comprueba que un valor '-' se interpreta como dato ausente (None), no como error."""
    resultado = normalizar_porcentaje("-")
    assert resultado is None


def test_normalizar_porcentaje_cero_real():
    """Comprueba que '0.00%' se interpreta como un cero real, y NO se confunde con dato ausente."""
    resultado = normalizar_porcentaje("0.00%")
    assert resultado == 0.0

    