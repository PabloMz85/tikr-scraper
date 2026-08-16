"""Modelos SQLAlchemy espejando el esquema de database/schema.sql."""
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Double, Integer, String, TIMESTAMP, DateTime, Text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


def _updated_at() -> sa.Column:
    return sa.Column(
        TIMESTAMP,
        server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )


class IncomeStatement(Base):
    __tablename__ = "income_statement"

    company: sa.Mapped[str] = mapped_column(String(255), primary_key=True)
    year: sa.Mapped[int] = mapped_column(Integer, primary_key=True)
    revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_revenues_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    cost_of_goods_sold: sa.Mapped[Optional[float]] = mapped_column(Double)
    gross_profit: sa.Mapped[Optional[float]] = mapped_column(Double)
    gross_profit_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    gross_profit_margin: sa.Mapped[Optional[float]] = mapped_column(Double)
    selling_general_admin_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    rd_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_operating_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    operating_income: sa.Mapped[Optional[float]] = mapped_column(Double)
    operating_income_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    operating_margin: sa.Mapped[Optional[float]] = mapped_column(Double)
    interest_expense: sa.Mapped[Optional[float]] = mapped_column(Double)
    interest_and_investment_income: sa.Mapped[Optional[float]] = mapped_column(Double)
    currency_exchange_gains_loss: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_non_operating_income_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    ebt_excl_unusual_items: sa.Mapped[Optional[float]] = mapped_column(Double)
    merger_restructuring_charges: sa.Mapped[Optional[float]] = mapped_column(Double)
    gain_loss_on_sale_of_investments: sa.Mapped[Optional[float]] = mapped_column(Double)
    gain_loss_on_sale_of_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    asset_writedown: sa.Mapped[Optional[float]] = mapped_column(Double)
    in_process_rd_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    legal_settlements: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_unusual_items: sa.Mapped[Optional[float]] = mapped_column(Double)
    ebt_incl_unusual_items: sa.Mapped[Optional[float]] = mapped_column(Double)
    income_tax_expense: sa.Mapped[Optional[float]] = mapped_column(Double)
    earnings_from_continuing_operations: sa.Mapped[Optional[float]] = mapped_column(Double)
    earnings_of_discontinued_operations: sa.Mapped[Optional[float]] = mapped_column(Double)
    extraordinary_item_accounting_change: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_income_to_company: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_income: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_income_to_common_incl_extra_items: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_income_to_common_incl_extra_items_margins: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_income_to_common_excl_extra_items: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_income_to_common_excl_extra_items_margins: sa.Mapped[Optional[float]] = mapped_column(Double)
    diluted_eps_excl_extra_items: sa.Mapped[Optional[float]] = mapped_column(Double)
    diluted_eps_excl_extra_items_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    weighted_average_diluted_shares_outstanding: sa.Mapped[Optional[float]] = mapped_column(Double)
    weighted_average_diluted_shares_outstanding_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    weighted_average_basic_shares_outstanding: sa.Mapped[Optional[float]] = mapped_column(Double)
    weighted_average_basic_shares_outstanding_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    dividends_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    dividends_per_share_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    payout_ratio: sa.Mapped[Optional[float]] = mapped_column(Double)
    basic_eps: sa.Mapped[Optional[float]] = mapped_column(Double)
    ebitda: sa.Mapped[Optional[float]] = mapped_column(Double)
    ebitda_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    ebitdar: sa.Mapped[Optional[float]] = mapped_column(Double)
    rd_expense: sa.Mapped[Optional[float]] = mapped_column(Double)
    selling_and_marketing_expense: sa.Mapped[Optional[float]] = mapped_column(Double)
    general_and_administrative_expense: sa.Mapped[Optional[float]] = mapped_column(Double)
    effective_tax_rate: sa.Mapped[Optional[float]] = mapped_column(Double)
    market_cap: sa.Mapped[Optional[float]] = mapped_column(Double)
    price_close: sa.Mapped[Optional[float]] = mapped_column(Double)
    TEV: sa.Mapped[Optional[float]] = mapped_column(Double)
    updated_at: sa.Mapped[Optional[sa.TIMESTAMP]] = _updated_at()


class CashflowStatement(Base):
    __tablename__ = "cashflow_statement"

    company: sa.Mapped[str] = mapped_column(String(255), primary_key=True)
    year: sa.Mapped[int] = mapped_column(Integer, primary_key=True)
    net_income: sa.Mapped[Optional[float]] = mapped_column(Double)
    depreciation_amortization: sa.Mapped[Optional[float]] = mapped_column(Double)
    amortization_of_goodwill_and_intangible_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    amortization_of_deferred_charges: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_depreciation_amortization: sa.Mapped[Optional[float]] = mapped_column(Double)
    gain_loss_from_sale_of_asset: sa.Mapped[Optional[float]] = mapped_column(Double)
    gain_loss_on_sale_of_investments: sa.Mapped[Optional[float]] = mapped_column(Double)
    asset_writedown_restructuring_costs: sa.Mapped[Optional[float]] = mapped_column(Double)
    stock_based_compensation: sa.Mapped[Optional[float]] = mapped_column(Double)
    tax_benefit_from_stock_options: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_cash_from_discontinued_operations: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_operating_activities: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_accounts_receivable: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_inventories: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_accounts_payable: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_unearned_revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_income_taxes: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_other_net_operating_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_from_operations: sa.Mapped[Optional[float]] = mapped_column(Double)
    change_in_net_working_capital: sa.Mapped[Optional[float]] = mapped_column(Double)
    capital_expenditure: sa.Mapped[Optional[float]] = mapped_column(Double)
    sale_of_property_plant_and_equipment: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_acquisitions: sa.Mapped[Optional[float]] = mapped_column(Double)
    divestitures: sa.Mapped[Optional[float]] = mapped_column(Double)
    sale_of_intangible_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    investment_in_marketable_and_equity_securities: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_investing_activities: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_from_investing: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_debt_issued: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_debt_repaid: sa.Mapped[Optional[float]] = mapped_column(Double)
    issuance_of_common_stock: sa.Mapped[Optional[float]] = mapped_column(Double)
    repurchase_of_common_stock: sa.Mapped[Optional[float]] = mapped_column(Double)
    common_dividends_paid: sa.Mapped[Optional[float]] = mapped_column(Double)
    common_preferred_stock_dividends_paid: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_financing_activities: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_from_financing: sa.Mapped[Optional[float]] = mapped_column(Double)
    foreign_exchange_rate_adjustments: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_change_in_cash: sa.Mapped[Optional[float]] = mapped_column(Double)
    free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    free_cash_flow_yoy: sa.Mapped[Optional[float]] = mapped_column(Double)
    free_cash_flow_margins: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_and_cash_equivalents_beginning_of_period: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_and_cash_equivalents_end_of_period: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_interest_paid: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_taxes_paid: sa.Mapped[Optional[float]] = mapped_column(Double)
    cash_flow_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    updated_at: sa.Mapped[Optional[sa.TIMESTAMP]] = _updated_at()


class BalancesheetStatement(Base):
    __tablename__ = "balancesheet_statement"

    company: sa.Mapped[str] = mapped_column(String(255), primary_key=True)
    year: sa.Mapped[int] = mapped_column(Integer, primary_key=True)
    cash_and_equivalents: sa.Mapped[Optional[float]] = mapped_column(Double)
    short_term_investments: sa.Mapped[Optional[float]] = mapped_column(Double)
    trading_asset_securities: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_cash_and_short_term_investments: sa.Mapped[Optional[float]] = mapped_column(Double)
    accounts_receivable: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_receivables: sa.Mapped[Optional[float]] = mapped_column(Double)
    notes_receivable: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_receivables: sa.Mapped[Optional[float]] = mapped_column(Double)
    inventory: sa.Mapped[Optional[float]] = mapped_column(Double)
    prepaid_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    deferred_tax_assets_current: sa.Mapped[Optional[float]] = mapped_column(Double)
    restricted_cash: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_current_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_current_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    gross_property_plant_and_equipment: sa.Mapped[Optional[float]] = mapped_column(Double)
    accumulated_depreciation: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_property_plant_and_equipment: sa.Mapped[Optional[float]] = mapped_column(Double)
    long_term_investments: sa.Mapped[Optional[float]] = mapped_column(Double)
    goodwill: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_intangibles: sa.Mapped[Optional[float]] = mapped_column(Double)
    loans_receivable_long_term: sa.Mapped[Optional[float]] = mapped_column(Double)
    deferred_tax_assets_long_term: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_long_term_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_assets: sa.Mapped[Optional[float]] = mapped_column(Double)
    accounts_payable: sa.Mapped[Optional[float]] = mapped_column(Double)
    accrued_expenses: sa.Mapped[Optional[float]] = mapped_column(Double)
    short_term_borrowings: sa.Mapped[Optional[float]] = mapped_column(Double)
    current_portion_of_long_term_debt: sa.Mapped[Optional[float]] = mapped_column(Double)
    current_portion_of_capital_lease_obligations: sa.Mapped[Optional[float]] = mapped_column(Double)
    current_income_taxes_payable: sa.Mapped[Optional[float]] = mapped_column(Double)
    unearned_revenue_current: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_current_liabilities: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_current_liabilities: sa.Mapped[Optional[float]] = mapped_column(Double)
    long_term_debt: sa.Mapped[Optional[float]] = mapped_column(Double)
    capital_leases: sa.Mapped[Optional[float]] = mapped_column(Double)
    unearned_revenue_non_current: sa.Mapped[Optional[float]] = mapped_column(Double)
    deferred_tax_liability_non_current: sa.Mapped[Optional[float]] = mapped_column(Double)
    other_non_current_liabilities: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_liabilities: sa.Mapped[Optional[float]] = mapped_column(Double)
    preferred_stock_redeemable: sa.Mapped[Optional[float]] = mapped_column(Double)
    preferred_stock_non_redeemable: sa.Mapped[Optional[float]] = mapped_column(Double)
    preferred_stock_convertible: sa.Mapped[Optional[float]] = mapped_column(Double)
    preferred_stock_others: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_preferred_equity: sa.Mapped[Optional[float]] = mapped_column(Double)
    common_stock: sa.Mapped[Optional[float]] = mapped_column(Double)
    additional_paid_in_capital: sa.Mapped[Optional[float]] = mapped_column(Double)
    retained_earnings: sa.Mapped[Optional[float]] = mapped_column(Double)
    comprehensive_income_and_other: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_common_equity: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_equity: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_liabilities_and_equity: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_shares_out_on_filing_date: sa.Mapped[Optional[float]] = mapped_column(Double)
    book_value_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    tangible_book_value: sa.Mapped[Optional[float]] = mapped_column(Double)
    tangible_book_value_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_debt: sa.Mapped[Optional[float]] = mapped_column(Double)
    net_debt: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_minority_interest: sa.Mapped[Optional[float]] = mapped_column(Double)
    equity_method_investments: sa.Mapped[Optional[float]] = mapped_column(Double)
    land: sa.Mapped[Optional[float]] = mapped_column(Double)
    buildings: sa.Mapped[Optional[float]] = mapped_column(Double)
    construction_in_progress: sa.Mapped[Optional[float]] = mapped_column(Double)
    full_time_employees: sa.Mapped[Optional[float]] = mapped_column(Double)
    updated_at: sa.Mapped[Optional[sa.TIMESTAMP]] = _updated_at()


class MultiplesStatement(Base):
    __tablename__ = "multiples_statement"

    company: sa.Mapped[str] = mapped_column(String(255), primary_key=True)
    year: sa.Mapped[int] = mapped_column(Integer, primary_key=True)
    ntm_total_enterprise_value_revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_price_sales_ps: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_total_enterprise_value_gross_profit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_total_enterprise_value_ebitda: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_total_enterprise_value_ebit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_price_normalized_earnings_pe: sa.Mapped[Optional[float]] = mapped_column(Double)
    peg_ratio: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_market_cap_free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_levered_free_cash_flow_yield: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_price_ffo_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_price_affo_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_dividend_yield: sa.Mapped[Optional[float]] = mapped_column(Double)
    trailing_multiples: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_total_enterprise_value_revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_price_sales_ps: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_total_enterprise_value_gross_profit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_total_enterprise_value_ebitda: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_total_enterprise_value_ebit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_price_diluted_eps_pe: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_price_book_value_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_price_tangible_book_value_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_total_enterprise_value_unlevered_free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_market_cap_levered_free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_price_net_current_asset_value: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_dividend_yield: sa.Mapped[Optional[float]] = mapped_column(Double)
    price_factors: sa.Mapped[Optional[float]] = mapped_column(Double)
    price: sa.Mapped[Optional[float]] = mapped_column(Double)
    total_enterprise_value_mm: sa.Mapped[Optional[float]] = mapped_column(Double)
    market_cap_mm: sa.Mapped[Optional[float]] = mapped_column(Double)
    forward_factors: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_gross_profit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_ebitda: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_ebit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_normalized_earnings_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_normalized_eps_yoy_growth: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_normalized_pe_multiple: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_gaap_earnings: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_dividend_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_levered_free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_distributable_cash_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_ffo_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_affo_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_bv_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ntm_nav_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    trailing_factors: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_revenues: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_gross_profit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_ebitda: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_ebit: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_diluted_eps_before_extra: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_book_value_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_tangible_book_value_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_dividend_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_unlevered_free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_levered_free_cash_flow: sa.Mapped[Optional[float]] = mapped_column(Double)
    ltm_net_current_asset_value_per_share: sa.Mapped[Optional[float]] = mapped_column(Double)
    updated_at: sa.Mapped[Optional[sa.TIMESTAMP]] = _updated_at()


class ApprovedUser(Base):
    __tablename__ = "approved_users"

    user_name: sa.Mapped[str] = mapped_column(String(255), primary_key=True)
    active: sa.Mapped[Optional[int]] = mapped_column(
        TINYINT, server_default=sa.text("1")
    )
    created_at: sa.Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
    )
    blocked_at: sa.Mapped[Optional[datetime]] = mapped_column(DateTime)
    released_at: sa.Mapped[Optional[datetime]] = mapped_column(DateTime)


# user_block_history y users_log no tienen PRIMARY KEY en el esquema real,
# por lo que no se mapean como clases ORM (requieren PK) sino como Table planas
# en el mismo MetaData, para que alembic autogenerate las vea.
sa.Table(
    "user_block_history",
    Base.metadata,
    sa.Column("user_name", String(255), nullable=False),
    sa.Column("blocked_at", DateTime),
    sa.Column("released_at", DateTime),
)

sa.Table(
    "users_log",
    Base.metadata,
    sa.Column("user_name", String(255), nullable=False),
    sa.Column("ip_address", String(45), nullable=False),
    sa.Column("token", Text),
    sa.Column("logged_at", DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    sa.Index("idx_user_name", "user_name"),
)
