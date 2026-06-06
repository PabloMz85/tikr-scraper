"""DB Utils"""
import os
import datetime
import sqlite3
from typing import List

python_path = './'
tikrDB_path = './data/tikrDB.db'
approved_users_path = './data/approved_users.db'
user_log_path = './data/user_logs.db'

def create_database() -> None:
    """
    Create the SQLite DB
    """
    os.makedirs(python_path + 'data', exist_ok=True)

    conn = sqlite3.connect(tikrDB_path)

    # Create a cursor object to execute queries
    cursor = conn.cursor()

    # Create the new income_statement table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income_statement (
        company TEXT,
        year INTEGER,
        revenues float,
        total_revenues float,
        total_revenues_yoy float,
        cost_of_goods_sold float,
        gross_profit float,
        gross_profit_yoy float,
        gross_profit_margin float,
        selling_general_admin_expenses float,
        rd_expenses float,
        total_operating_expenses float,
        operating_income float,
        operating_income_yoy float,
        operating_margin float,
        interest_expense float,
        interest_and_investment_income float,
        currency_exchange_gains_loss float,
        other_non_operating_income_expenses float,
        ebt_excl_unusual_items float,
        merger_restructuring_charges float,
        gain_loss_on_sale_of_investments float,
        gain_loss_on_sale_of_assets float,
        asset_writedown float,
        in_process_rd_expenses float,
        legal_settlements float,
        other_unusual_items float,
        ebt_incl_unusual_items float,
        income_tax_expense float,
        earnings_from_continuing_operations float,
        earnings_of_discontinued_operations float,
        extraordinary_item_accounting_change float,
        net_income_to_company float,
        net_income float,
        net_income_to_common_incl_extra_items float,
        net_income_to_common_incl_extra_items_margins float,
        net_income_to_common_excl_extra_items float,
        net_income_to_common_excl_extra_items_margins float,
        diluted_eps_excl_extra_items float,
        diluted_eps_excl_extra_items_yoy float,
        weighted_average_diluted_shares_outstanding float,
        weighted_average_diluted_shares_outstanding_yoy float,
        weighted_average_basic_shares_outstanding float,
        weighted_average_basic_shares_outstanding_yoy float,
        dividends_per_share float,
        dividends_per_share_yoy float,
        payout_ratio float,
        basic_eps float,
        ebitda float,
        ebitda_yoy float,
        ebitdar float,
        rd_expense float,
        selling_and_marketing_expense float,
        general_and_administrative_expense float,
        effective_tax_rate float,
        market_cap float,
        price_close float,
        TEV float,
        PRIMARY KEY (company, year)
        );
    ''')

    # Create the new cashflow_statement table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cashflow_statement (
        company TEXT,
        year INTEGER,
        net_income float,
        depreciation_amortization float,
        amortization_of_goodwill_and_intangible_assets float,
        amortization_of_deferred_charges float,
        total_depreciation_amortization float,
        gain_loss_from_sale_of_asset float,
        gain_loss_on_sale_of_investments float,
        asset_writedown_restructuring_costs float,
        stock_based_compensation float,
        tax_benefit_from_stock_options float,
        net_cash_from_discontinued_operations float,
        other_operating_activities float,
        change_in_accounts_receivable float,
        change_in_inventories float,
        change_in_accounts_payable float,
        change_in_unearned_revenues float,
        change_in_income_taxes float,
        change_in_other_net_operating_assets float,
        cash_from_operations float,
        change_in_net_working_capital float,
        capital_expenditure float,
        sale_of_property_plant_and_equipment float,
        cash_acquisitions float,
        divestitures float,
        sale_of_intangible_assets float,
        investment_in_marketable_and_equity_securities float,
        other_investing_activities float,
        cash_from_investing float,
        total_debt_issued float,
        total_debt_repaid float,
        issuance_of_common_stock float,
        repurchase_of_common_stock float,
        common_dividends_paid float,
        common_preferred_stock_dividends_paid float,
        other_financing_activities float,
        cash_from_financing float,
        foreign_exchange_rate_adjustments float,
        net_change_in_cash float,
        free_cash_flow float,
        free_cash_flow_yoy float,
        free_cash_flow_margins float,
        cash_and_cash_equivalents_beginning_of_period float,
        cash_and_cash_equivalents_end_of_period float,
        cash_interest_paid float,
        cash_taxes_paid float,
        cash_flow_per_share float,
        PRIMARY KEY (company, year)
        );
    ''')

    # Create the new balancesheet_statement table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balancesheet_statement (
        company TEXT,
        year INTEGER,
        cash_and_equivalents float,
        short_term_investments float,
        trading_asset_securities float,
        total_cash_and_short_term_investments float,
        accounts_receivable float,
        other_receivables float,
        notes_receivable float,
        total_receivables float,
        inventory float,
        prepaid_expenses float,
        deferred_tax_assets_current float,
        restricted_cash float,
        other_current_assets float,
        total_current_assets float,
        gross_property_plant_and_equipment float,
        accumulated_depreciation float,
        net_property_plant_and_equipment float,
        long_term_investments float,
        goodwill float,
        other_intangibles float,
        loans_receivable_long_term float,
        deferred_tax_assets_long_term float,
        other_long_term_assets float,
        total_assets float,
        accounts_payable float,
        accrued_expenses float,
        short_term_borrowings float,
        current_portion_of_long_term_debt float,
        current_portion_of_capital_lease_obligations float,
        current_income_taxes_payable float,
        unearned_revenue_current float,
        other_current_liabilities float,
        total_current_liabilities float,
        long_term_debt float,
        capital_leases float,
        unearned_revenue_non_current float,
        deferred_tax_liability_non_current float,
        other_non_current_liabilities float,
        total_liabilities float,
        preferred_stock_redeemable float,
        preferred_stock_non_redeemable float,
        preferred_stock_convertible float,
        preferred_stock_others float,
        total_preferred_equity float,
        common_stock float,
        additional_paid_in_capital float,
        retained_earnings float,
        comprehensive_income_and_other float,
        total_common_equity float,
        total_equity float,
        total_liabilities_and_equity float,
        total_shares_out_on_filing_date float,
        book_value_share float,
        tangible_book_value float,
        tangible_book_value_share float,
        total_debt float,
        net_debt float,
        total_minority_interest float,
        equity_method_investments float,
        land float,
        buildings float,
        construction_in_progress float,
        full_time_employees float,
        PRIMARY KEY (company, year)
        );
    ''')

    # Create the new multiples_statement table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS multiples_statement (
        company TEXT,
        year INTEGER,
        ntm_total_enterprise_value_revenues float,
        ntm_price_sales_ps float,
        ntm_total_enterprise_value_gross_profit float,
        ntm_total_enterprise_value_ebitda float,
        ntm_total_enterprise_value_ebit float,
        ntm_price_normalized_earnings_pe float,
        peg_ratio float,
        ntm_market_cap_free_cash_flow float,
        ntm_levered_free_cash_flow_yield float,
        ntm_price_ffo_per_share float,
        ntm_price_affo_per_share float,
        ntm_dividend_yield float,
        trailing_multiples float,
        ltm_total_enterprise_value_revenues float,
        ltm_price_sales_ps float,
        ltm_total_enterprise_value_gross_profit float,
        ltm_total_enterprise_value_ebitda float,
        ltm_total_enterprise_value_ebit float,
        ltm_price_diluted_eps_pe float,
        ltm_price_book_value_per_share float,
        ltm_price_tangible_book_value_per_share float,
        ltm_total_enterprise_value_unlevered_free_cash_flow float,
        ltm_market_cap_levered_free_cash_flow float,
        ltm_price_net_current_asset_value float,
        ltm_dividend_yield float,
        price_factors float,
        price float,
        total_enterprise_value_mm float,
        market_cap_mm float,
        forward_factors float,
        ntm_gross_profit float,
        ntm_revenues float,
        ntm_ebitda float,
        ntm_ebit float,
        ntm_normalized_earnings_per_share float,
        ntm_normalized_eps_yoy_growth float,
        ntm_normalized_pe_multiple float,
        ntm_gaap_earnings float,
        ntm_dividend_share float,
        ntm_levered_free_cash_flow float,
        ntm_distributable_cash_per_share float,
        ntm_ffo_per_share float,
        ntm_affo_per_share float,
        ntm_bv_per_share float,
        ntm_nav_per_share float,
        trailing_factors float,
        ltm_revenues float,
        ltm_gross_profit float,
        ltm_ebitda float,
        ltm_ebit float,
        ltm_diluted_eps_before_extra float,
        ltm_book_value_per_share float,
        ltm_tangible_book_value_per_share float,
        ltm_dividend_per_share float,
        ltm_unlevered_free_cash_flow float,
        ltm_levered_free_cash_flow float,
        ltm_net_current_asset_value_per_share float,
        PRIMARY KEY (company, year)
        );
    ''')

    # Close the connection with tikrDB
    conn.close()


    conn = sqlite3.connect(approved_users_path)
    # Create a cursor object to execute queries
    cursor = conn.cursor()

    # Create the approved_users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS approved_users (
            user_number TEXT PRIMARY KEY,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            blocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            released_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Close the connection with approved_users
    conn.close()


    conn = sqlite3.connect(user_log_path)
    # Create a cursor object to execute queries
    cursor = conn.cursor()
    
    # Create the users_log table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_log (
            user_number TEXT,
            ip_address TEXT,
            token TEXT,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Close the connection
    conn.close()

def insert_or_update_data(table: str, data: List[dict]) -> None:
    """
    Inserta o actualiza registros en la tabla especificada.
    Usa 'ON CONFLICT(company, year)' para hacer UPSERT automático.
    """
    conn = sqlite3.connect(tikrDB_path)
    cursor = conn.cursor()

    for record in data:
        company = record.get("company")
        year = record.get("year")

        if not company or not year:
            print(f"Registro sin company o year: {record}")
            continue

        # Generar dinámicamente los nombres de columnas
        columns = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))

        # Construir parte del UPDATE dinámico (sin company/year)
        update_clause = ', '.join([f"{col}=excluded.{col}" for col in record.keys() if col not in ("company", "year")])

        # UPSERT automático: si ya existe (company, year), actualiza solo las columnas
        sql = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            ON CONFLICT(company, year) DO UPDATE SET
            {update_clause};
        """

        cursor.execute(sql, list(record.values()))

    conn.commit()
    conn.close()

def list_users() -> list:
    """
    Returns all users.
    """
    conn = sqlite3.connect(approved_users_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approved_users")
    rows = cursor.fetchall()
    conn.close()

    # 1. Extracción de los nombres de las columnas desde los metadatos del cursor
    # cursor.description retorna una tupla de tuplas donde el índice 0 es el nombre de la columna.
    nombres_columnas = [descripcion[0] for descripcion in cursor.description]

    # 2. Emparejamiento iterativo (Zipping)
    # Se fusionan los nombres de las columnas con los valores de cada fila,
    # garantizando estructuras de longitud 2 (par clave-valor) para el constructor dict().
    lista_diccionarios = [
        dict(zip(nombres_columnas, fila)) 
        for fila in rows
    ]

    return lista_diccionarios

def is_user_approved(user_number: str) -> bool:
    """
    Returns True if the given user_number exists and is active in approved_users.
    """
    if not user_number:
        return False
    conn = sqlite3.connect(approved_users_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM approved_users WHERE user_number = ? AND active = 1", (user_number,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def add_approved_user(user_number: str) -> None:
    """
    Adds a user_number to the approved_users table. Idempotent (ignores duplicates).
    """
    if not user_number:
        return
    conn = sqlite3.connect(approved_users_path)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().isoformat()
    cursor.execute("INSERT OR IGNORE INTO approved_users (user_number, active, created_at) VALUES (?, 1, ?)", (user_number, created_at))
    conn.commit()
    conn.close()

def block_user(user_number: str) -> None:
    """
    Block a user_number by setting active = 0.
    """
    if not user_number:
        return
    conn = sqlite3.connect(approved_users_path)
    cursor = conn.cursor()
    blocked_at = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE approved_users SET active = 0 and blocked_at = ? WHERE user_number = ?", (blocked_at, user_number))
    conn.commit()
    conn.close()

def unblock_user(user_number: str) -> None:
    """
    Unblock a user_number by setting active = 1.
    """
    if not user_number:
        return
    conn = sqlite3.connect(approved_users_path)
    cursor = conn.cursor()
    unblocked_at = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE approved_users SET active = 0 and unblocked_at = ? WHERE user_number = ?", (unblocked_at, user_number))
    conn.commit()
    conn.close()

def log_user_activity(user_number: str, ip_address: str, token: str) -> None:
    """
    Log user activity in the users_log table.
    """
    if not user_number or not ip_address:
        return
    conn = sqlite3.connect(user_log_path)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO users_log (user_number, ip_address, token, logged_at) VALUES (?, ?, ?, ?)", (user_number, ip_address, token, timestamp))
    conn.commit()
    conn.close()