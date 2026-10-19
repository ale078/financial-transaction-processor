"""Extractor for Mercado Pago annual yield and holding reports (PDF)."""

from pathlib import Path
from typing import Dict, Any, List
import pdfplumber
import re

from src.extractors.base_extractor import BaseExtractor

class MercadoPagoExtractor(BaseExtractor):
    """Processes Mercado Pago Reporte de Tenencia y Rendimientos PDF files."""

    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".pdf":
            return False
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    return False
                first_page = pdf.pages[0].extract_text() or ""
                return "mercado pago" in first_page.lower() or "mercado fondo" in first_page.lower() or "mercadolibre" in first_page.lower()
        except Exception:
            return False

    def extract(self) -> Dict[str, Any]:
        balances: List[Dict[str, Any]] = []
        holdings: List[Dict[str, Any]] = []
        transactions: List[Dict[str, Any]] = []

        total_available_ars = 0.0
        total_reservas_ars = 0.0
        fci_cuotapartes = 0.0
        fci_valor_cuota = 0.0
        rendimientos_2025 = 0.0
        cvu = ""
        cuit = ""
        owner = "ALEJANDRO JOSE ROMAGNOLI"

        with pdfplumber.open(self.file_path) as pdf:
            full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

            # Owner & CVU
            cvu_match = re.search(r"CVU:\s*([0-9]+)", full_text)
            if cvu_match:
                cvu = cvu_match.group(1)
            cuit_match = re.search(r"CUIT/CUIL:\s*([0-9]+)", full_text)
            if cuit_match:
                cuit = cuit_match.group(1)

            # Available Cash
            disp_match = re.search(r"dinero disponible:\s*\$\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            if disp_match:
                total_available_ars = self.parse_float(disp_match.group(1))

            # Reserves
            res_match = re.search(r"reservas:\s*\$\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            if res_match:
                total_reservas_ars = self.parse_float(res_match.group(1))

            # Cuotapartes
            cuotas_match = re.search(r"cuotapartes:\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            if cuotas_match:
                fci_cuotapartes = self.parse_float(cuotas_match.group(1))

            valor_match = re.search(r"Valor de cuotapartes:\s*\$\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            if valor_match:
                fci_valor_cuota = self.parse_float(valor_match.group(1))

            # Rendimientos Acumulados
            rend_match = re.search(r"dinero invertido:\s*\$\s*([0-9\.\,]+)", full_text, re.IGNORECASE)
            if rend_match:
                rendimientos_2025 = self.parse_float(rend_match.group(1))

        # Balances
        balances.append({
            "institution": "Mercado Pago",
            "account_type": "Dinero Disponible (Remunerado)",
            "account_number": cvu or "0000003100061672740443",
            "currency": "ARS",
            "balance": total_available_ars,
            "balance_ars": total_available_ars,
            "balance_usd": 0.0
        })

        if total_reservas_ars > 0:
            balances.append({
                "institution": "Mercado Pago",
                "account_type": "Reservas",
                "account_number": "Reservas MP",
                "currency": "ARS",
                "balance": total_reservas_ars,
                "balance_ars": total_reservas_ars,
                "balance_usd": 0.0
            })

        # Holdings
        if total_available_ars > 0:
            holdings.append({
                "ticker": "MP-FCI-BIND",
                "description": "Fondo Común Mercado Fondo (BIND) - Saldo Remunerado",
                "asset_class": "Liquidez Remunerada",
                "institution": "Mercado Pago",
                "quantity": fci_cuotapartes if fci_cuotapartes > 0 else total_available_ars,
                "currency": "ARS",
                "unit_price": fci_valor_cuota if fci_valor_cuota > 0 else 1.0,
                "total_value_ars": total_available_ars,
                "account_id": cvu,
                "extra_info": {
                    "yield_earned_2025": rendimientos_2025,
                    "cuotapartes": fci_cuotapartes,
                    "valor_cuota": fci_valor_cuota
                }
            })

        if total_reservas_ars > 0:
            holdings.append({
                "ticker": "MP-RESERVAS",
                "description": "Reservas Mercado Pago",
                "asset_class": "Reservas",
                "institution": "Mercado Pago",
                "quantity": total_reservas_ars,
                "currency": "ARS",
                "unit_price": 1.0,
                "total_value_ars": total_reservas_ars,
                "account_id": cvu
            })

        # Transaction for the earned yield in 2025
        if rendimientos_2025 > 0:
            transactions.append({
                "date": "2025-12-31",
                "institution": "Mercado Pago",
                "account_or_ticker": "MP-FCI-BIND",
                "description": "Rendimientos Anuales Acumulados FCI Mercado Fondo BIND",
                "amount": rendimientos_2025,
                "currency": "ARS",
                "category": "Rendimiento",
                "tx_type": "Yield",
                "source_file": self.file_path.name
            })

        return {
            "institution": "Mercado Pago",
            "owner": owner,
            "cvu": cvu,
            "cuit": cuit,
            "balances": balances,
            "holdings": holdings,
            "transactions": transactions,
            "extra": {
                "rendimientos_2025": rendimientos_2025,
                "cuotapartes": fci_cuotapartes,
                "valor_cuotaparte": fci_valor_cuota,
                "reservas": total_reservas_ars
            }
        }
