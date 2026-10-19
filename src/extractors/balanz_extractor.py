"""Extractor for Balanz Capital consolidated statements (PDF)."""

from pathlib import Path
from typing import Dict, Any, List
import pdfplumber
import re

from src.extractors.base_extractor import BaseExtractor

class BalanzExtractor(BaseExtractor):
    """Processes Balanz Capital Posición Consolidada PDF files."""

    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".pdf":
            return False
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    return False
                first_page = pdf.pages[0].extract_text() or ""
                return "balanz" in first_page.lower()
        except Exception:
            return False

    def extract(self) -> Dict[str, Any]:
        balances: List[Dict[str, Any]] = []
        holdings: List[Dict[str, Any]] = []
        transactions: List[Dict[str, Any]] = []

        total_portfolio_ars = 0.0
        fx_mep = 1480.46
        fx_ccl = 1520.07

        with pdfplumber.open(self.file_path) as pdf:
            full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

            # 1. Parse FX rates from text
            mep_match = re.search(r"MEP\s*\$\s*([0-9\.\,]+)", full_text)
            if mep_match:
                fx_mep = self.parse_float(mep_match.group(1))

            ccl_match = re.search(r"US Dollar\s*\$\s*([0-9\.\,]+)", full_text)
            if ccl_match:
                fx_ccl = self.parse_float(ccl_match.group(1))

            # 2. Parse Total and Balances on Page 1
            tot_match = re.search(r"Total\s*\$\s*([0-9\.\,]+)", full_text)
            if tot_match:
                total_portfolio_ars = self.parse_float(tot_match.group(1))

            ars_match = re.search(r"Pesos\s*\$\s*([0-9\.\,]+)", full_text)
            cash_ars = self.parse_float(ars_match.group(1)) if ars_match else 0.0

            usd_match = re.search(r"D[a-záéíóú\s]+USD\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            cash_usd = self.parse_float(usd_match.group(1)) if usd_match else 0.0

            cable_match = re.search(r"Cable\)?\s*USD\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            cash_cable = self.parse_float(cable_match.group(1)) if cable_match else 0.0

            balances.append({
                "institution": "Balanz Capital",
                "account_type": "Cuenta Comitente Pesos",
                "account_number": "299946",
                "currency": "ARS",
                "balance": cash_ars,
                "balance_ars": cash_ars,
                "balance_usd": round(cash_ars / fx_mep, 2) if fx_mep else 0.0
            })
            if cash_ars > 0:
                holdings.append({
                    "ticker": "ARS-BALANZ",
                    "description": "Liquidez en Pesos Balanz Capital (Cta 299946)",
                    "asset_class": "Dinero a la vista",
                    "institution": "Balanz Capital",
                    "quantity": cash_ars,
                    "currency": "ARS",
                    "unit_price": 1.0,
                    "total_value_ars": cash_ars,
                    "total_value_usd": round(cash_ars / fx_mep, 2)
                })

            if cash_usd > 0:
                usd_val_ars = cash_usd * fx_mep
                balances.append({
                    "institution": "Balanz Capital",
                    "account_type": "Cuenta Comitente USD MEP",
                    "account_number": "299946",
                    "currency": "USD",
                    "balance": cash_usd,
                    "balance_ars": usd_val_ars,
                    "balance_usd": cash_usd
                })
                holdings.append({
                    "ticker": "USD-MEP-BALANZ",
                    "description": "Dólares MEP en Cuenta Balanz Capital",
                    "asset_class": "Dinero a la vista",
                    "institution": "Balanz Capital",
                    "quantity": cash_usd,
                    "currency": "USD",
                    "unit_price": fx_mep,
                    "total_value_ars": usd_val_ars,
                    "total_value_usd": cash_usd
                })

            if cash_cable > 0:
                cable_val_ars = cash_cable * fx_ccl
                balances.append({
                    "institution": "Balanz Capital",
                    "account_type": "Cuenta Comitente USD Cable",
                    "account_number": "299946",
                    "currency": "USD Cable",
                    "balance": cash_cable,
                    "balance_ars": cable_val_ars,
                    "balance_usd": cash_cable
                })
                holdings.append({
                    "ticker": "USD-CCL-BALANZ",
                    "description": "Dólares Cable en Cuenta Balanz Capital",
                    "asset_class": "Dinero a la vista",
                    "institution": "Balanz Capital",
                    "quantity": cash_cable,
                    "currency": "USD Cable",
                    "unit_price": fx_ccl,
                    "total_value_ars": cable_val_ars,
                    "total_value_usd": cash_cable
                })

            # 3. Parse Holdings Sections (Bonos, Cedears, Corporativos, Fondos)
            current_category = None
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = text.splitlines()

                for line in lines:
                    line_s = line.strip()
                    if not line_s:
                        continue

                    # Section Header detection
                    if line_s.lower() == "bonos":
                        current_category = "Bonos Soberanos"
                        continue
                    elif line_s.lower() == "cedears":
                        current_category = "Cedears"
                        continue
                    elif line_s.lower() == "corporativos":
                        current_category = "Corporativos / ON"
                        continue
                    elif line_s.lower() == "fondos":
                        current_category = "Fondos Comunes"
                        continue

                    if current_category and "Especie" not in line_s and "BALANZ" not in line_s and "Distribuci" not in line_s:
                        # Row pattern: TICKER DESCRIPTION CANTIDAD GARANTIA PRECIO VALOR_ACTUAL
                        # e.g.: CP34O ON CIA GEN.COMB. CL.34 V23/02/26 US$ CG 3.000,00 0.00 $ 1.520,00 $ 4.560.000
                        row_pattern = r"^([A-Z0-9]{3,7})\s+(.+?)\s+([0-9\.\,]+)\s+([0-9\.\,]+)\s+\$\s*([0-9\.\,]+)\s+\$\s*([0-9\.\,]+)$"
                        match = re.match(row_pattern, line_s)
                        if match:
                            ticker, desc, qty_str, _, price_str, val_str = match.groups()
                            qty = self.parse_float(qty_str)
                            price = self.parse_float(price_str)
                            val_ars = self.parse_float(val_str)

                            holdings.append({
                                "ticker": ticker.strip(),
                                "description": desc.strip(),
                                "asset_class": current_category,
                                "institution": "Balanz Capital",
                                "quantity": qty,
                                "currency": "ARS",
                                "unit_price": price,
                                "total_value_ars": val_ars,
                                "total_value_usd": round(val_ars / fx_mep, 2) if fx_mep else 0.0,
                                "account_id": "299946"
                            })

        return {
            "institution": "Balanz Capital",
            "owner": "ROMAGNOLI ALEJANDRO JOSE",
            "account_number": "299946",
            "total_portfolio_ars": total_portfolio_ars,
            "fx_mep": fx_mep,
            "fx_ccl": fx_ccl,
            "balances": balances,
            "holdings": holdings,
            "transactions": transactions,
            "extra": {
                "fx_mep": fx_mep,
                "fx_ccl": fx_ccl,
                "total_declared": total_portfolio_ars
            }
        }
