"""Base class and helper functions for financial extractors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from dateutil import parser as date_parser

class BaseExtractor(ABC):
    """Abstract base class for all institution statement extractors."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    @classmethod
    @abstractmethod
    def can_handle(cls, file_path: Path) -> bool:
        """Determines if this extractor is suitable for the given file."""
        pass

    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        """Extracts holdings, balances, and movements from the file.
        
        Returns a dictionary containing:
        - institution: str
        - holdings: List[Dict]
        - balances: List[Dict]
        - transactions: List[Dict]
        - extra: Dict (rates, yields, plazos fijos, metadata)
        """
        pass

    @staticmethod
    def parse_float(val: Any) -> float:
        """Safely parses Argentine/international formatted currency strings to float."""
        if val is None or val == "":
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        
        s = str(val).strip()
        # Remove currency symbols and non-breaking spaces
        s = re.sub(r"[\$\€\£\s\xa0USDu\$s]", "", s, flags=re.IGNORECASE)
        
        if not s:
            return 0.0

        # Handle negative in parenthesis: (123.45)
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1].strip()
        elif s.startswith("-"):
            is_negative = True
            s = s[1:].strip()

        # Check dots and commas
        if "." in s and "," in s:
            if s.rfind(",") > s.rfind("."):
                # Argentine standard: 1.234.567,89
                s = s.replace(".", "").replace(",", ".")
            else:
                # US standard: 1,234,567.89
                s = s.replace(",", "")
        elif "," in s:
            # Single or multiple commas: check if thousand separators or decimal
            if s.count(",") > 1:
                s = s.replace(",", "")
            else:
                # e.g., 999,50 -> 999.50
                s = s.replace(",", ".")
        elif "." in s:
            # Only dots present
            parts = s.split(".")
            if len(parts) > 2:
                # Multiple dots: clearly thousand separators e.g. 6.431.783
                s = "".join(parts)
            elif len(parts) == 2:
                # Single dot: if exactly 3 digits after dot (e.g. 146.760, 502.762, 300.400), it's a thousand separator
                if len(parts[1]) == 3 and len(parts[0]) <= 3:
                    s = parts[0] + parts[1]
                else:
                    # Decimal representation e.g. 22.1502 or 0.00
                    pass
            
        try:
            res = float(s)
            return -res if is_negative else res
        except ValueError:
            return 0.0

    @staticmethod
    def parse_date_str(val: Any) -> str:
        """Converts diverse date expressions into YYYY-MM-DD."""
        if val is None or val == "":
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d")
        
        s = str(val).strip()
        # Common Spanish month mapping
        months = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
        }
        for m_name, m_num in months.items():
            if m_name in s.lower():
                s = re.sub(m_name, m_num, s, flags=re.IGNORECASE)

        try:
            dt = date_parser.parse(s, fuzzy=True, dayfirst=True)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return str(val)[:10]
