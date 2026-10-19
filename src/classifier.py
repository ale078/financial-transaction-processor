"""Rule-based and keyword-driven financial transaction classifier tailored for personal and investment accounts."""

from typing import Tuple
import re

CATEGORIES = {
    "Sueldo y Honorarios": [
        "cash sueldos", "sueldo", "haberes", "honorarios", "remuneracion", "consult en tecno", "nomina"
    ],
    "Inversiones - Plazos Fijos": [
        "plazo fijo", "vto. plazo fijo", "con.pf", "constitucion plazo fijo", "interes capitalizado"
    ],
    "Inversiones - Fondos (FCI)": [
        "fima", "suscripcion fima", "rescate fima", "ualintec", "mercado fondo", "cuotapartes", "fci"
    ],
    "Inversiones - Títulos y Valores": [
        "boleto", "cpra", "venta", "al30", "gd38", "ethaim", "etha", "googl", "alua", "txar",
        "dividendo", "renta y amortizacion", "cobro de renta", "custodia"
    ],
    "Rendimientos y Ganancias": [
        "rendimiento", "interes", "intereses", "yield", "dividendo", "ganancia"
    ],
    "Servicios Públicos y Hogar": [
        "personal flow", "metrogas", "edenor", "edesur", "aysa", "flow", "telecom", "gas", "luz", "agua", "internet"
    ],
    "Tarjetas y Pagos Financieros": [
        "tarjeta", "visa", "mastercard", "pago tarjeta", "debito tarjeta"
    ],
    "Transferencias Propias y Cuentas": [
        "transf. ctas propias", "transferencia propia", "traspaso de saldo", "recibo de cobro", "comprobante de pago"
    ],
    "Extracciones en Efectivo": [
        "extraccion cajero", "extraccion atm", "cajero automatico", "retiro efectivo", "banelco", "link"
    ],
    "Impuestos y Tasas": [
        "afip", "arba", "agip", "impuesto", "iva", "sircreb", "debito fiscal", "credito fiscal", "ley 25413"
    ]
}

class TransactionClassifier:
    """Classifies transaction descriptions into standard personal finance categories."""

    def __init__(self, custom_rules: dict = None):
        self.rules = CATEGORIES.copy()
        if custom_rules:
            self.rules.update(custom_rules)

    def classify(self, description: str, amount: float = 0.0) -> Tuple[str, str]:
        """
        Classifies a transaction description.
        Returns:
            Tuple of (Category, TransactionType: 'Income' | 'Expense' | 'Investment' | 'Transfer')
        """
        desc_clean = (description or "").lower()

        # Check keyword matches
        for category, keywords in self.rules.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", desc_clean) or kw in desc_clean:
                    # Specific transaction type based on category
                    if "Sueldo" in category or "Rendimientos" in category:
                        tx_type = "Income"
                    elif "Plazos Fijos" in category or "Fondos" in category or "Títulos" in category:
                        if "vto" in desc_clean or "rescate" in desc_clean or "venta" in desc_clean or "dividendo" in desc_clean:
                            tx_type = "Income"
                        else:
                            tx_type = "Investment"
                    elif "Transferencias" in category:
                        tx_type = "Transfer"
                    elif amount < 0 or "debito" in desc_clean or "pago" in desc_clean:
                        tx_type = "Expense"
                    else:
                        tx_type = "Income" if amount > 0 else "Expense"
                    return category, tx_type

        # Fallback category
        if amount > 0:
            return "Otros Ingresos", "Income"
        elif amount < 0:
            return "Gastos Varios", "Expense"
        return "Movimientos Generales", "Transfer"
