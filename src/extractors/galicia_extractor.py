"""Extractor for Banco Galicia consolidated statements and tax summaries (Excel)."""

from pathlib import Path
from typing import Dict, Any, List
import openpyxl

from src.extractors.base_extractor import BaseExtractor

class GaliciaExtractor(BaseExtractor):
    """Processes Banco Galicia Taxation & Consolidated Position Excel files."""

    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        if file_path.suffix.lower() not in [".xlsx", ".xls"]:
            return False
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            for sname in wb.sheetnames:
                if "posici" in sname.lower() or "taxation" in sname.lower():
                    return True
            return False
        except Exception:
            return False

    def extract(self) -> Dict[str, Any]:
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = wb.worksheets[0]

        balances: List[Dict[str, Any]] = []
        holdings: List[Dict[str, Any]] = []
        transactions: List[Dict[str, Any]] = []
        plazos_fijos: List[Dict[str, Any]] = []
        plazos_fijos_results: List[Dict[str, Any]] = []

        total_cuentas_pesificado = self.parse_float(ws.cell(16, 67).value)
        total_inversiones_pesificado = self.parse_float(ws.cell(39, 52).value)

        # 1. Accounts & Balances (Rows 22-34)
        caja_ahorro_ars = self.parse_float(ws.cell(29, 53).value)
        caja_ahorro_usd = self.parse_float(ws.cell(32, 53).value)
        cta_cte_ars = self.parse_float(ws.cell(34, 53).value)

        balances.append({
            "institution": "Banco Galicia",
            "account_type": "Caja de Ahorro",
            "account_number": "4001716-7 664-3",
            "currency": "ARS",
            "balance": caja_ahorro_ars,
            "balance_ars": caja_ahorro_ars,
            "balance_usd": 0.0
        })
        balances.append({
            "institution": "Banco Galicia",
            "account_type": "Cuenta Corriente",
            "account_number": "0000959-5 664-6",
            "currency": "ARS",
            "balance": cta_cte_ars,
            "balance_ars": cta_cte_ars,
            "balance_usd": 0.0
        })
        balances.append({
            "institution": "Banco Galicia",
            "account_type": "Caja de Ahorro Dólares",
            "account_number": "4001247-5 664-9",
            "currency": "USD",
            "balance": caja_ahorro_usd,
            "balance_ars": caja_ahorro_usd,
            "balance_usd": caja_ahorro_usd
        })

        # Add balances to holdings as liquid asset
        if caja_ahorro_ars > 0:
            holdings.append({
                "ticker": "ARS-GALICIA-CA",
                "description": "Caja de Ahorro en Pesos Banco Galicia (4001716-7)",
                "asset_class": "Dinero a la vista",
                "institution": "Banco Galicia",
                "quantity": caja_ahorro_ars,
                "currency": "ARS",
                "unit_price": 1.0,
                "total_value_ars": caja_ahorro_ars,
                "account_id": "4001716-7"
            })
        if cta_cte_ars > 0:
            holdings.append({
                "ticker": "ARS-GALICIA-CC",
                "description": "Cuenta Corriente en Pesos Banco Galicia (0000959-5)",
                "asset_class": "Dinero a la vista",
                "institution": "Banco Galicia",
                "quantity": cta_cte_ars,
                "currency": "ARS",
                "unit_price": 1.0,
                "total_value_ars": cta_cte_ars,
                "account_id": "0000959-5"
            })

        # 2. Plazos Fijos Vigentes (Rows 47-51)
        for r in range(47, 52):
            pf_nro = str(ws.cell(r, 36).value or "").strip()
            if not pf_nro:
                continue
            f_ini = self.parse_date_str(ws.cell(r, 43).value)
            f_vto = self.parse_date_str(ws.cell(r, 50).value)
            plazo_dias = int(ws.cell(r, 61).value or 30)
            capital = self.parse_float(ws.cell(r, 68).value)
            tasa = self.parse_float(ws.cell(r, 90).value)
            devengado = self.parse_float(ws.cell(r, 107).value or ws.cell(r, 100).value)
            al_vencimiento = self.parse_float(ws.cell(r, 116).value)

            val_actual = devengado if devengado > 0 else capital
            holdings.append({
                "ticker": f"PF-{pf_nro[-6:]}",
                "description": f"Plazo Fijo Tradicional Tasa {tasa}% (Vto: {f_vto})",
                "asset_class": "Plazos Fijos",
                "institution": "Banco Galicia",
                "quantity": 1.0,
                "currency": "ARS",
                "unit_price": val_actual,
                "total_value_ars": val_actual,
                "extra_info": {
                    "number": pf_nro,
                    "capital": capital,
                    "rate_tna": tasa,
                    "start_date": f_ini,
                    "end_date": f_vto,
                    "plazo_days": plazo_dias,
                    "maturity_amount": al_vencimiento
                }
            })
            plazos_fijos.append({
                "number": pf_nro,
                "start_date": f_ini,
                "end_date": f_vto,
                "capital": capital,
                "rate_tna": tasa,
                "accrued_amount": devengado,
                "maturity_amount": al_vencimiento,
                "status": "Vigente"
            })

        # 3. Fondos Comunes de Inversión (Row 54)
        fci_name = str(ws.cell(54, 29).value or "FIMA PREMIUM CLASE A").strip()
        fci_cuotas = self.parse_float(ws.cell(54, 51).value)
        fci_precio = self.parse_float(ws.cell(54, 63).value)
        fci_monto = self.parse_float(ws.cell(54, 92).value)
        if fci_monto > 0:
            holdings.append({
                "ticker": "FIMA-PREM-A",
                "description": fci_name,
                "asset_class": "Fondos Comunes",
                "institution": "Banco Galicia",
                "quantity": fci_cuotas,
                "currency": "ARS",
                "unit_price": fci_precio,
                "total_value_ars": fci_monto,
                "extra_info": {"fund": fci_name, "account": "2810874"}
            })

        # 4. Resultados Anuales Plazos Fijos (Rows 236-272)
        total_intereses_percibidos = 0.0
        for r in range(236, 273):
            pf_num = str(ws.cell(r, 37).value or "").strip()
            if not pf_num:
                continue
            f_ini = self.parse_date_str(ws.cell(r, 46).value)
            f_vto = self.parse_date_str(ws.cell(r, 53).value)
            tasa = self.parse_float(ws.cell(r, 66).value)
            plazo = int(ws.cell(r, 72).value or 30)
            saldo_final = self.parse_float(ws.cell(r, 97).value)
            interes = self.parse_float(ws.cell(r, 105).value)
            total_intereses_percibidos += interes

            plazos_fijos_results.append({
                "number": pf_num,
                "start_date": f_ini,
                "end_date": f_vto,
                "rate_tna": tasa,
                "days": plazo,
                "final_balance": saldo_final,
                "interest_earned": interes
            })

        # 5. Bank Transactions (Rows 69-223)
        for r in range(69, 224):
            raw_fec = ws.cell(r, 26).value
            raw_ley = ws.cell(r, 36).value
            if not raw_fec or not raw_ley:
                continue
            date_str = self.parse_date_str(raw_fec)
            concept = str(raw_ley).strip()
            debito = self.parse_float(ws.cell(r, 48).value)
            credito = self.parse_float(ws.cell(r, 56).value)

            amount = credito - debito
            tx_type = "Inflow" if amount >= 0 else "Outflow"

            transactions.append({
                "date": date_str,
                "institution": "Banco Galicia",
                "account_or_ticker": "Caja de Ahorro $",
                "description": concept,
                "amount": amount,
                "currency": "ARS",
                "tx_type": tx_type,
                "source_file": self.file_path.name
            })

        return {
            "institution": "Banco Galicia",
            "owner": "ALEJANDRO JOSE ROMAGNOLI",
            "cuit": "20266293101",
            "balances": balances,
            "holdings": holdings,
            "transactions": transactions,
            "plazos_fijos": plazos_fijos,
            "plazos_fijos_results": plazos_fijos_results,
            "extra": {
                "total_cuentas": total_cuentas_pesificado,
                "total_inversiones": total_inversiones_pesificado,
                "total_intereses_ganados": total_intereses_percibidos
            }
        }
