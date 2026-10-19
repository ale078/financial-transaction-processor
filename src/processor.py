"""Bridge processor delegating to the unified PortfolioConsolidator."""

from pathlib import Path
import pandas as pd
from src.consolidator import PortfolioConsolidator

class TransactionProcessor:
    """Backward compatibility wrapper delegating to PortfolioConsolidator."""

    def __init__(self, input_dir: str | Path):
        self.input_dir = Path(input_dir)
        self.consolidator = PortfolioConsolidator(input_dir=self.input_dir)

    def process_all(self) -> pd.DataFrame:
        """Processes files and returns a transactions DataFrame for legacy calls."""
        portfolio = self.consolidator.process()
        rows = [
            {
                "Date": t.date,
                "Institution": t.institution,
                "Account_Or_Ticker": t.account_or_ticker,
                "Description": t.description,
                "Amount": t.amount,
                "Currency": t.currency,
                "Category": t.category,
                "Type": t.tx_type,
                "Source File": t.source_file
            }
            for t in portfolio.transactions
        ]
        return pd.DataFrame(rows)
