"""Main entry point for Financial Transaction & Portfolio Consolidator."""

import sys
import argparse
from pathlib import Path
from src.consolidator import PortfolioConsolidator
from src.exporter import ExcelExporter

def main():
    parser = argparse.ArgumentParser(description="Consolidador Financiero y Dashboard Personal")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Inicia el servidor local y abre el Dashboard web en el navegador")
    parser.add_argument("--port", "-p", type=int, default=8050, help="Puerto para el servidor del dashboard (default: 8050)")
    args = parser.parse_args()

    print("==========================================================")
    print("      CONSOLIDADOR FINANCIERO Y PATRIMONIAL PERSONAL     ")
    print("==========================================================\n")

    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"

    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    print(f"[*] Carpeta de Entrada (Input):  {input_dir}")
    print(f"[*] Carpeta de Salida (Output): {output_dir}\n")

    # Run consolidation
    consolidator = PortfolioConsolidator(input_dir=input_dir)
    portfolio = consolidator.process()

    if not portfolio.holdings and not portfolio.balances:
        print("\n[!] No se pudieron extraer datos financieros.")
        print("    Asegúrate de colocar los archivos Excel (.xlsx) y PDF de tus bancos y brokers en 'input/'.")
        sys.exit(0)

    # Print summary
    print(f"[+] Procesamiento completado para: {portfolio.owner_name}")
    print(f"    - Archivos analizados:        {len(portfolio.source_files)}")
    print(f"    - Total Patrimonio (ARS):    ${portfolio.total_net_worth_ars:,.2f}")
    print(f"    - Total Patrimonio (USD MEP): USD {portfolio.total_net_worth_usd:,.2f} (TC: ${portfolio.fx_rate_mep:,.2f})")
    print(f"    - Liquidez Inmediata:        ${portfolio.total_liquidity_ars:,.2f}")
    print(f"    - Activos Invertidos:        ${portfolio.total_invested_ars:,.2f}")
    print(f"    - Rendimientos / Intereses:  ${portfolio.total_earned_yields_ars:,.2f}")

    print("\n--- Desglose por Institución Financiera ---")
    for name, s in portfolio.institutions.items():
        print(f"    • {name:<18}: ${s.total_ars:>14,.2f} ({s.share_pct:>5.1f}%) | {s.holdings_count} activos")

    # Export Excel
    exporter = ExcelExporter(output_dir=output_dir)
    report_file = exporter.export(portfolio)
    print(f"\n[OK] Reporte Excel generado con éxito:")
    print(f"     -> {report_file.name}")
    print("==========================================================")

    if args.dashboard:
        from dashboard_server import start_server
        start_server(port=args.port, auto_open=True)

if __name__ == "__main__":
    main()
