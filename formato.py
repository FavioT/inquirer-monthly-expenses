def formatear_monto(monto: float) -> str:
    """Formatea un importe con punto para miles y coma para decimales."""
    return f"${monto:,.2f}".translate(str.maketrans({",": ".", ".": ","}))
