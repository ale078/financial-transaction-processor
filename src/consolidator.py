"""Core consolidator module unifying bank statements, brokers, and fintech wallets."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from src.models import (
    Holding, AccountBalance, Transaction, PlazoFijoItem,
    InstitutionSummary, ConsolidatedPortfolio
)
from src.extractors import (
    ALL_EXTRACTORS, GaliciaExtractor, BalanzExtractor,
    MercadoPagoExtractor, UalaExtractor
)
from src.classifier import TransactionClassifier

class PortfolioConsolidator:
    """Discovers consolidated financial statements, extracts data, and creates a unified portfolio snapshot."""

    def __init__(self, input_dir: str | Path):
        self.input_dir = Path(input_dir)
        self.classifier = TransactionClassifier()

    def process(self) -> ConsolidatedPortfolio:
        """Processes all input files and returns a unified ConsolidatedPortfolio object."""
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")

        files = sorted(self.input_dir.glob("*.*"))
        supported_files = [f for f in files if f.suffix.lower() in [".xlsx", ".xls", ".pdf", ".csv"]]

        all_holdings_raw: List[Dict[str, Any]] = []
        all_balances_raw: List[Dict[str, Any]] = []
        all_tx_raw: List[Dict[str, Any]] = []
        all_pfs: List[PlazoFijoItem] = []
        source_file_names: List[str] = []

        fx_mep = 1480.46
        fx_ccl = 1520.07
        total_yields_ars = 0.0

        for file_path in supported_files:
            matched_extractor_cls = None
            for ext_cls in ALL_EXTRACTORS:
                try:
                    if ext_cls.can_handle(file_path):
                        matched_extractor_cls = ext_cls
                        break
                except Exception:
                    continue

            if not matched_extractor_cls:
                continue

            try:
                extractor = matched_extractor_cls(file_path)
                data = extractor.extract()
                source_file_names.append(file_path.name)

                # Capture FX rates if available
                if "fx_mep" in data and data["fx_mep"]:
                    fx_mep = float(data["fx_mep"])
                if "fx_ccl" in data and data["fx_ccl"]:
                    fx_ccl = float(data["fx_ccl"])

                # Yields
                if "extra" in data:
                    extra = data["extra"]
                    if "total_intereses_ganados" in extra:
                        total_yields_ars += float(extra["total_intereses_ganados"])
                    if "rendimientos_2025" in extra:
                        total_yields_ars += float(extra["rendimientos_2025"])

                # Plazos Fijos
                if "plazos_fijos" in data:
                    for pf in data["plazos_fijos"]:
                        all_pfs.append(PlazoFijoItem(
                            number=pf["number"],
                            start_date=pf["start_date"],
                            end_date=pf["end_date"],
                            capital=pf["capital"],
                            rate_tna=pf["rate_tna"],
                            accrued_amount=pf["accrued_amount"],
                            maturity_amount=pf["maturity_amount"],
                            status=pf.get("status", "Vigente")
                        ))

                # Holdings
                all_holdings_raw.extend(data.get("holdings", []))

                # Balances
                all_balances_raw.extend(data.get("balances", []))

                # Transactions
                all_tx_raw.extend(data.get("transactions", []))

            except Exception as e:
                print(f"[CONSOLIDATOR ERROR] Could not process {file_path.name}: {e}")

        # Compute Holdings
        holdings_list: List[Holding] = []
        for h in all_holdings_raw:
            val_ars = float(h.get("total_value_ars", 0.0))
            val_usd = float(h.get("total_value_usd", 0.0))
            if val_usd == 0.0 and fx_mep > 0:
                val_usd = round(val_ars / fx_mep, 2)

            holdings_list.append(Holding(
                ticker=h.get("ticker", "N/A"),
                description=h.get("description", ""),
                asset_class=h.get("asset_class", "Otros"),
                institution=h.get("institution", "Desconocido"),
                quantity=float(h.get("quantity", 1.0)),
                currency=h.get("currency", "ARS"),
                unit_price=float(h.get("unit_price", 0.0)),
                total_value_ars=val_ars,
                total_value_usd=val_usd,
                account_id=h.get("account_id"),
                extra_info=h.get("extra_info", {})
            ))

        # Sort holdings by valuation descending
        holdings_list.sort(key=lambda x: x.total_value_ars, reverse=True)

        # Compute Balances
        balances_list: List[AccountBalance] = []
        for b in all_balances_raw:
            b_ars = float(b.get("balance_ars", 0.0))
            b_usd = float(b.get("balance_usd", 0.0))
            if b_usd == 0.0 and fx_mep > 0 and b_ars > 0:
                b_usd = round(b_ars / fx_mep, 2)
            balances_list.append(AccountBalance(
                institution=b.get("institution", ""),
                account_type=b.get("account_type", ""),
                account_number=b.get("account_number", ""),
                currency=b.get("currency", "ARS"),
                balance=float(b.get("balance", 0.0)),
                balance_ars=b_ars,
                balance_usd=b_usd
            ))

        # Compute Transactions with Classification
        tx_list: List[Transaction] = []
        for t in all_tx_raw:
            amt = float(t.get("amount", 0.0))
            desc = t.get("description", "")
            cat = t.get("category")
            ttype = t.get("tx_type")

            if not cat or not ttype:
                detected_cat, detected_ttype = self.classifier.classify(desc, amt)
                cat = cat or detected_cat
                ttype = ttype or detected_ttype

            tx_list.append(Transaction(
                date=t.get("date", ""),
                institution=t.get("institution", ""),
                account_or_ticker=t.get("account_or_ticker", ""),
                description=desc,
                amount=amt,
                currency=t.get("currency", "ARS"),
                category=cat,
                tx_type=ttype,
                source_file=t.get("source_file", "")
            ))

        # Sort transactions chronologically
        tx_list.sort(key=lambda x: x.date, reverse=True)

        # Portfolio Aggregations
        total_ars = sum(h.total_value_ars for h in holdings_list)
        total_usd = round(total_ars / fx_mep, 2) if fx_mep else 0.0

        # Assign weights
        for h in holdings_list:
            h.weight_pct = round((h.total_value_ars / total_ars) * 100, 2) if total_ars else 0.0

        # Breakdowns by Asset Class
        asset_classes: Dict[str, float] = {}
        for h in holdings_list:
            ac = h.asset_class
            asset_classes[ac] = round(asset_classes.get(ac, 0.0) + h.total_value_ars, 2)

        # Breakdowns by Institution
        inst_groups: Dict[str, List[Holding]] = {}
        for h in holdings_list:
            inst_groups.setdefault(h.institution, []).append(h)

        institutions_summary: Dict[str, InstitutionSummary] = {}
        for inst_name, inst_holdings in inst_groups.items():
            inst_ars = sum(h.total_value_ars for h in inst_holdings)
            inst_usd = round(inst_ars / fx_mep, 2) if fx_mep else 0.0
            inst_share = round((inst_ars / total_ars) * 100, 2) if total_ars else 0.0

            liquidity_ars = sum(h.total_value_ars for h in inst_holdings if h.asset_class in ["Dinero a la vista", "Liquidez Remunerada", "Reservas"])
            invested_ars = inst_ars - liquidity_ars

            ac_breakdown: Dict[str, float] = {}
            for h in inst_holdings:
                ac_breakdown[h.asset_class] = round(ac_breakdown.get(h.asset_class, 0.0) + h.total_value_ars, 2)

            institutions_summary[inst_name] = InstitutionSummary(
                name=inst_name,
                total_ars=round(inst_ars, 2),
                total_usd=inst_usd,
                share_pct=inst_share,
                liquidity_ars=round(liquidity_ars, 2),
                invested_ars=round(invested_ars, 2),
                asset_classes_breakdown=ac_breakdown,
                holdings_count=len(inst_holdings)
            )

        liquidity_total = sum(h.total_value_ars for h in holdings_list if h.asset_class in ["Dinero a la vista", "Liquidez Remunerada", "Reservas"])
        invested_total = total_ars - liquidity_total

        return ConsolidatedPortfolio(
            owner_name="ALEJANDRO JOSE ROMAGNOLI",
            period_label="Posición Consolidada 2025 / 2026",
            fx_rate_mep=fx_mep,
            fx_rate_ccl=fx_ccl,
            total_net_worth_ars=round(total_ars, 2),
            total_net_worth_usd=total_usd,
            total_liquidity_ars=round(liquidity_total, 2),
            total_invested_ars=round(invested_total, 2),
            total_earned_yields_ars=round(total_yields_ars, 2),
            total_debt_ars=0.0,
            institutions=institutions_summary,
            asset_classes=asset_classes,
            holdings=holdings_list,
            balances=balances_list,
            transactions=tx_list,
            plazos_fijos=all_pfs,
            source_files=source_file_names
        )

    def to_dict(self, portfolio: ConsolidatedPortfolio) -> Dict[str, Any]:
        """Converts the ConsolidatedPortfolio dataclass into a JSON-serializable dictionary."""
        return {
            "owner_name": portfolio.owner_name,
            "period_label": portfolio.period_label,
            "fx_rate_mep": portfolio.fx_rate_mep,
            "fx_rate_ccl": portfolio.fx_rate_ccl,
            "total_net_worth_ars": portfolio.total_net_worth_ars,
            "total_net_worth_usd": portfolio.total_net_worth_usd,
            "total_liquidity_ars": portfolio.total_liquidity_ars,
            "total_invested_ars": portfolio.total_invested_ars,
            "total_earned_yields_ars": portfolio.total_earned_yields_ars,
            "total_debt_ars": portfolio.total_debt_ars,
            "institutions": {
                name: {
                    "name": s.name,
                    "total_ars": s.total_ars,
                    "total_usd": s.total_usd,
                    "share_pct": s.share_pct,
                    "liquidity_ars": s.liquidity_ars,
                    "invested_ars": s.invested_ars,
                    "asset_classes_breakdown": s.asset_classes_breakdown,
                    "holdings_count": s.holdings_count
                }
                for name, s in portfolio.institutions.items()
            },
            "asset_classes": portfolio.asset_classes,
            "holdings": [
                {
                    "ticker": h.ticker,
                    "description": h.description,
                    "asset_class": h.asset_class,
                    "institution": h.institution,
                    "quantity": h.quantity,
                    "currency": h.currency,
                    "unit_price": h.unit_price,
                    "total_value_ars": h.total_value_ars,
                    "total_value_usd": h.total_value_usd,
                    "weight_pct": h.weight_pct,
                    "account_id": h.account_id,
                    "extra_info": h.extra_info
                }
                for h in portfolio.holdings
            ],
            "balances": [
                {
                    "institution": b.institution,
                    "account_type": b.account_type,
                    "account_number": b.account_number,
                    "currency": b.currency,
                    "balance": b.balance,
                    "balance_ars": b.balance_ars,
                    "balance_usd": b.balance_usd
                }
                for b in portfolio.balances
            ],
            "transactions": [
                {
                    "date": t.date,
                    "institution": t.institution,
                    "account_or_ticker": t.account_or_ticker,
                    "description": t.description,
                    "amount": t.amount,
                    "currency": t.currency,
                    "category": t.category,
                    "tx_type": t.tx_type,
                    "source_file": t.source_file
                }
                for t in portfolio.transactions
            ],
            "plazos_fijos": [
                {
                    "number": pf.number,
                    "start_date": pf.start_date,
                    "end_date": pf.end_date,
                    "capital": pf.capital,
                    "rate_tna": pf.rate_tna,
                    "accrued_amount": pf.accrued_amount,
                    "maturity_amount": pf.maturity_amount,
                    "status": pf.status
                }
                for pf in portfolio.plazos_fijos
            ],
            "source_files": portfolio.source_files
        }
