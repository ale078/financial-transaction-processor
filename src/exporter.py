"""Executive Excel exporter generating formatted multi-sheet financial portfolios."""

from pathlib import Path
from typing import Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from src.models import ConsolidatedPortfolio

class ExcelExporter:
    """Exports consolidated personal portfolio snapshot to a polished multi-tab Excel workbook."""

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, portfolio: ConsolidatedPortfolio, filename: str = "Patrimonio_Consolidado_Alejandro.xlsx") -> Path:
        out_file = self.output_dir / filename
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # Palettes
        NAVY_FILL = PatternFill(start_color="1A2035", end_color="1A2035", fill_type="solid")
        PURPLE_FILL = PatternFill(start_color="4C1D95", end_color="4C1D95", fill_type="solid")
        CARD_BG = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        ZEBRA_FILL = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="1E1B4B")
        KPI_LABEL_FONT = Font(name="Calibri", size=9, bold=False, color="64748B")
        KPI_VALUE_FONT = Font(name="Calibri", size=14, bold=True, color="0F172A")
        BOLD_FONT = Font(name="Calibri", size=11, bold=True)
        REG_FONT = Font(name="Calibri", size=11)
        THIN_BORDER = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1")
        )

        # -------------------------------------------------------------
        # 1. TAB: RESUMEN EJECUTIVO
        # -------------------------------------------------------------
        ws1 = wb.create_sheet(title="Resumen Ejecutivo")
        ws1.views.sheetView[0].showGridLines = True

        ws1["B2"] = "CONSOLIDADO PATRIMONIAL Y CUENTAS PERSONALES"
        ws1["B2"].font = TITLE_FONT
        ws1["B3"] = f"Titular: {portfolio.owner_name} | Período: {portfolio.period_label} | TC MEP: ${portfolio.fx_rate_mep:,.2f}"
        ws1["B3"].font = Font(name="Calibri", size=10, italic=True, color="475569")

        # KPI Cards (Row 5 to 7)
        kpis = [
            ("Patrimonio Total (ARS)", f"${portfolio.total_net_worth_ars:,.2f}", "B"),
            ("Patrimonio Total (USD)", f"USD {portfolio.total_net_worth_usd:,.2f}", "D"),
            ("Liquidez Inmediata", f"${portfolio.total_liquidity_ars:,.2f}", "F"),
            ("Activos Invertidos", f"${portfolio.total_invested_ars:,.2f}", "H"),
            ("Rendimientos 2025", f"${portfolio.total_earned_yields_ars:,.2f}", "J")
        ]
        for label, val, col in kpis:
            c_lbl = ws1[f"{col}5"]
            c_lbl.value = label
            c_lbl.font = KPI_LABEL_FONT
            c_lbl.fill = CARD_BG
            c_lbl.alignment = Alignment(horizontal="center", vertical="center")

            c_val = ws1[f"{col}6"]
            c_val.value = val
            c_val.font = KPI_VALUE_FONT
            c_val.fill = CARD_BG
            c_val.alignment = Alignment(horizontal="center", vertical="center")

        # Table: Resumen por Entidad Financiera (Row 9)
        ws1["B9"] = "DISTRIBUCIÓN POR INSTITUCIÓN FINANCIERA"
        ws1["B9"].font = Font(name="Calibri", size=12, bold=True, color="1E1B4B")

        inst_headers = ["Institución", "Total ARS", "Equivalente USD", "Participación %", "Liquidez ARS", "Invertido ARS", "Posiciones"]
        for col_idx, h in enumerate(inst_headers, start=2):
            cell = ws1.cell(row=11, column=col_idx, value=h)
            cell.fill = PURPLE_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center" if col_idx > 2 else "left")

        curr_r = 12
        for inst_name, s in portfolio.institutions.items():
            ws1.cell(row=curr_r, column=2, value=inst_name).font = BOLD_FONT
            
            c_ars = ws1.cell(row=curr_r, column=3, value=s.total_ars)
            c_ars.number_format = '$ #,##0.00'
            
            c_usd = ws1.cell(row=curr_r, column=4, value=s.total_usd)
            c_usd.number_format = 'USD #,##0.00'

            c_pct = ws1.cell(row=curr_r, column=5, value=s.share_pct / 100.0)
            c_pct.number_format = '0.0%'

            c_liq = ws1.cell(row=curr_r, column=6, value=s.liquidity_ars)
            c_liq.number_format = '$ #,##0.00'

            c_inv = ws1.cell(row=curr_r, column=7, value=s.invested_ars)
            c_inv.number_format = '$ #,##0.00'

            c_cnt = ws1.cell(row=curr_r, column=8, value=s.holdings_count)
            c_cnt.alignment = Alignment(horizontal="center")

            for c in range(2, 9):
                ws1.cell(row=curr_r, column=c).border = THIN_BORDER
                if curr_r % 2 == 1:
                    ws1.cell(row=curr_r, column=c).fill = ZEBRA_FILL
            curr_r += 1

        # Table: Resumen por Clase de Activo (Row curr_r + 2)
        curr_r += 2
        ws1.cell(row=curr_r, column=2, value="DISTRIBUCIÓN POR CLASE DE ACTIVO").font = Font(name="Calibri", size=12, bold=True, color="1E1B4B")
        curr_r += 2

        ac_headers = ["Clase de Activo", "Valuación Total ARS", "Equivalente USD", "Participación %"]
        for col_idx, h in enumerate(ac_headers, start=2):
            cell = ws1.cell(row=curr_r, column=col_idx, value=h)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center" if col_idx > 2 else "left")

        curr_r += 1
        for ac_name, val_ars in sorted(portfolio.asset_classes.items(), key=lambda x: x[1], reverse=True):
            ws1.cell(row=curr_r, column=2, value=ac_name).font = REG_FONT

            c_ars = ws1.cell(row=curr_r, column=3, value=val_ars)
            c_ars.number_format = '$ #,##0.00'

            val_usd = val_ars / portfolio.fx_rate_mep if portfolio.fx_rate_mep else 0.0
            c_usd = ws1.cell(row=curr_r, column=4, value=val_usd)
            c_usd.number_format = 'USD #,##0.00'

            share_pct = (val_ars / portfolio.total_net_worth_ars) if portfolio.total_net_worth_ars else 0.0
            c_pct = ws1.cell(row=curr_r, column=5, value=share_pct)
            c_pct.number_format = '0.0%'

            for c in range(2, 6):
                ws1.cell(row=curr_r, column=c).border = THIN_BORDER
                if curr_r % 2 == 1:
                    ws1.cell(row=curr_r, column=c).fill = ZEBRA_FILL
            curr_r += 1

        # -------------------------------------------------------------
        # 2. TAB: TENENCIAS Y PORTAFOLIO
        # -------------------------------------------------------------
        ws2 = wb.create_sheet(title="Tenencias y Portafolio")
        ws2.views.sheetView[0].showGridLines = True

        t_headers = ["Ticker / Identificador", "Descripción / Especie", "Clase de Activo", "Institución", "Cantidad", "Moneda", "Precio Unitario", "Valuación ARS", "Valuación USD", "Ponderación %"]
        for col_idx, h in enumerate(t_headers, start=1):
            cell = ws2.cell(row=1, column=col_idx, value=h)
            cell.fill = PURPLE_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

        for r_idx, h in enumerate(portfolio.holdings, start=2):
            ws2.cell(row=r_idx, column=1, value=h.ticker).font = BOLD_FONT
            ws2.cell(row=r_idx, column=2, value=h.description).font = REG_FONT
            ws2.cell(row=r_idx, column=3, value=h.asset_class).font = REG_FONT
            ws2.cell(row=r_idx, column=4, value=h.institution).font = REG_FONT

            c_qty = ws2.cell(row=r_idx, column=5, value=h.quantity)
            c_qty.number_format = '#,##0.00'

            ws2.cell(row=r_idx, column=6, value=h.currency).alignment = Alignment(horizontal="center")

            c_pr = ws2.cell(row=r_idx, column=7, value=h.unit_price)
            c_pr.number_format = '$ #,##0.00' if h.currency == 'ARS' else '#,##0.00'

            c_ars = ws2.cell(row=r_idx, column=8, value=h.total_value_ars)
            c_ars.number_format = '$ #,##0.00'

            c_usd = ws2.cell(row=r_idx, column=9, value=h.total_value_usd)
            c_usd.number_format = 'USD #,##0.00'

            c_wt = ws2.cell(row=r_idx, column=10, value=h.weight_pct / 100.0)
            c_wt.number_format = '0.00%'

            for c in range(1, 11):
                ws2.cell(row=r_idx, column=c).border = THIN_BORDER
                if r_idx % 2 == 1:
                    ws2.cell(row=r_idx, column=c).fill = ZEBRA_FILL

        # -------------------------------------------------------------
        # 3. TAB: SALDOS Y CUENTAS
        # -------------------------------------------------------------
        ws3 = wb.create_sheet(title="Saldos Monetarios")
        ws3.views.sheetView[0].showGridLines = True

        b_headers = ["Institución", "Tipo de Cuenta", "Nro de Cuenta", "Moneda Original", "Saldo Original", "Saldo Valuado ARS", "Saldo Valuado USD"]
        for col_idx, h in enumerate(b_headers, start=1):
            cell = ws3.cell(row=1, column=col_idx, value=h)
            cell.fill = NAVY_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

        for r_idx, b in enumerate(portfolio.balances, start=2):
            ws3.cell(row=r_idx, column=1, value=b.institution).font = BOLD_FONT
            ws3.cell(row=r_idx, column=2, value=b.account_type).font = REG_FONT
            ws3.cell(row=r_idx, column=3, value=b.account_number).font = REG_FONT
            ws3.cell(row=r_idx, column=4, value=b.currency).alignment = Alignment(horizontal="center")

            c_orig = ws3.cell(row=r_idx, column=5, value=b.balance)
            c_orig.number_format = '#,##0.00'

            c_ars = ws3.cell(row=r_idx, column=6, value=b.balance_ars)
            c_ars.number_format = '$ #,##0.00'

            c_usd = ws3.cell(row=r_idx, column=7, value=b.balance_usd)
            c_usd.number_format = 'USD #,##0.00'

            for c in range(1, 8):
                ws3.cell(row=r_idx, column=c).border = THIN_BORDER
                if r_idx % 2 == 1:
                    ws3.cell(row=r_idx, column=c).fill = ZEBRA_FILL

        # -------------------------------------------------------------
        # 4. TAB: MOVIMIENTOS Y TRANSACCIONES
        # -------------------------------------------------------------
        ws4 = wb.create_sheet(title="Movimientos y Transacciones")
        ws4.views.sheetView[0].showGridLines = True

        m_headers = ["Fecha", "Institución", "Cuenta / Especie", "Descripción / Concepto", "Categoría", "Tipo", "Monto", "Moneda", "Archivo Origen"]
        for col_idx, h in enumerate(m_headers, start=1):
            cell = ws4.cell(row=1, column=col_idx, value=h)
            cell.fill = PURPLE_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

        for r_idx, t in enumerate(portfolio.transactions, start=2):
            ws4.cell(row=r_idx, column=1, value=t.date).alignment = Alignment(horizontal="center")
            ws4.cell(row=r_idx, column=2, value=t.institution).font = REG_FONT
            ws4.cell(row=r_idx, column=3, value=t.account_or_ticker).font = REG_FONT
            ws4.cell(row=r_idx, column=4, value=t.description).font = REG_FONT
            ws4.cell(row=r_idx, column=5, value=t.category).font = BOLD_FONT
            ws4.cell(row=r_idx, column=6, value=t.tx_type).alignment = Alignment(horizontal="center")

            c_amt = ws4.cell(row=r_idx, column=7, value=t.amount)
            c_amt.number_format = '$ #,##0.00' if t.currency == 'ARS' else '#,##0.00'
            if t.amount < 0:
                c_amt.font = Font(name="Calibri", size=11, color="991B1B")
            else:
                c_amt.font = Font(name="Calibri", size=11, color="166534")

            ws4.cell(row=r_idx, column=8, value=t.currency).alignment = Alignment(horizontal="center")
            ws4.cell(row=r_idx, column=9, value=t.source_file).font = Font(name="Calibri", size=9, color="64748B")

            for c in range(1, 10):
                ws4.cell(row=r_idx, column=c).border = THIN_BORDER
                if r_idx % 2 == 1:
                    ws4.cell(row=r_idx, column=c).fill = ZEBRA_FILL

        # -------------------------------------------------------------
        # 5. TAB: PLAZOS FIJOS
        # -------------------------------------------------------------
        if portfolio.plazos_fijos:
            ws5 = wb.create_sheet(title="Plazos Fijos Vigentes")
            ws5.views.sheetView[0].showGridLines = True

            pf_headers = ["Nro Operación", "Fecha Constitución", "Fecha Vencimiento", "Capital Invertido", "Tasa TNA %", "Monto Devengado", "Monto al Vencimiento", "Estado"]
            for col_idx, h in enumerate(pf_headers, start=1):
                cell = ws5.cell(row=1, column=col_idx, value=h)
                cell.fill = NAVY_FILL
                cell.font = HEADER_FONT
                cell.alignment = Alignment(horizontal="center")

            for r_idx, pf in enumerate(portfolio.plazos_fijos, start=2):
                ws5.cell(row=r_idx, column=1, value=pf.number).font = BOLD_FONT
                ws5.cell(row=r_idx, column=2, value=pf.start_date).alignment = Alignment(horizontal="center")
                ws5.cell(row=r_idx, column=3, value=pf.end_date).alignment = Alignment(horizontal="center")

                c_cap = ws5.cell(row=r_idx, column=4, value=pf.capital)
                c_cap.number_format = '$ #,##0.00'

                c_tasa = ws5.cell(row=r_idx, column=5, value=pf.rate_tna / 100.0)
                c_tasa.number_format = '0.0%'

                c_dev = ws5.cell(row=r_idx, column=6, value=pf.accrued_amount)
                c_dev.number_format = '$ #,##0.00'

                c_mat = ws5.cell(row=r_idx, column=7, value=pf.maturity_amount)
                c_mat.number_format = '$ #,##0.00'

                ws5.cell(row=r_idx, column=8, value=pf.status).alignment = Alignment(horizontal="center")

                for c in range(1, 9):
                    ws5.cell(row=r_idx, column=c).border = THIN_BORDER
                    if r_idx % 2 == 1:
                        ws5.cell(row=r_idx, column=c).fill = ZEBRA_FILL

        # Auto-adjust column widths across all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    if cell.value:
                        lines = str(cell.value).split("\n")
                        max_len = max(max_len, max(len(l) for l in lines))
                sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 48)

        wb.save(out_file)
        return out_file
