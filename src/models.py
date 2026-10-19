"""Data models for consolidated personal finances and investments."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Holding:
    """Represents an investment holding (bond, equity, cedear, mutual fund, etc.)."""
    ticker: str
    description: str
    asset_class: str          # Corporativos / ON, Bonos Soberanos, Cedears, Acciones, Fondos Comunes, Plazo Fijo, Dinero a la vista, Reservas
    institution: str          # Balanz, Galicia, Mercado Pago, Uala
    quantity: float
    currency: str             # ARS, USD, USD Cable
    unit_price: float
    total_value_ars: float
    total_value_usd: float = 0.0
    weight_pct: float = 0.0
    account_id: Optional[str] = None
    extra_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AccountBalance:
    """Represents a bank account or wallet cash balance."""
    institution: str
    account_type: str         # Caja de Ahorro, Cuenta Corriente, Billetera Virtual, Cuenta Comitente
    account_number: str
    currency: str             # ARS, USD, USD Cable
    balance: float
    balance_ars: float
    balance_usd: float = 0.0

@dataclass
class Transaction:
    """Represents a unified cash movement, trade, or dividend."""
    date: str
    institution: str
    account_or_ticker: str
    description: str
    amount: float             # positive = credit/inflow, negative = debit/outflow
    currency: str
    category: str             # Sueldo, Inversión, Dividendo/Renta, Rendimiento, Plazo Fijo, Servicio, Tarjeta, Transferencia, etc.
    tx_type: str              # Inflow, Outflow, Investment, Yield
    source_file: str = ""

@dataclass
class PlazoFijoItem:
    """Represents a fixed-term deposit with interest data."""
    number: str
    start_date: str
    end_date: str
    capital: float
    rate_tna: float
    accrued_amount: float
    maturity_amount: float
    earned_interest: float = 0.0
    status: str = "Vigente"   # Vigente or Finalizado

@dataclass
class InstitutionSummary:
    """Summary of assets in a specific financial institution."""
    name: str
    total_ars: float
    total_usd: float
    share_pct: float
    liquidity_ars: float
    invested_ars: float
    asset_classes_breakdown: Dict[str, float] = field(default_factory=dict)
    account_count: int = 0
    holdings_count: int = 0

@dataclass
class ConsolidatedPortfolio:
    """Full unified portfolio snapshot across all institutions."""
    owner_name: str
    period_label: str
    fx_rate_mep: float
    fx_rate_ccl: float
    total_net_worth_ars: float
    total_net_worth_usd: float
    total_liquidity_ars: float
    total_invested_ars: float
    total_earned_yields_ars: float
    total_debt_ars: float
    institutions: Dict[str, InstitutionSummary] = field(default_factory=dict)
    asset_classes: Dict[str, float] = field(default_factory=dict)
    holdings: List[Holding] = field(default_factory=list)
    balances: List[AccountBalance] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    plazos_fijos: List[PlazoFijoItem] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
