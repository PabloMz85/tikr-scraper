from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime
import json
import re
import requests
import time
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class scraper_utils:

    #################################################################
    # Functions to get data from TIKR API or from local test files
    #################################################################

    def create_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")               # Obligatorio en Docker
        chrome_options.add_argument("--disable-dev-shm-usage")    # Evita problemas de memoria compartida
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")

        # User agent opcional
        user_agent = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) '
                    'Chrome/22.0.1216.0 Safari/537.2')
        chrome_options.add_argument(f'user-agent={user_agent}')

        # Detecta si estamos en Docker y usar Chromium si está disponible
        chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
        if os.path.exists(chrome_bin):
            chrome_options.binary_location = chrome_bin

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def get_access_token() -> str:
        username = os.environ['TIKR_ACCOUNT_USERNAME']
        password = os.environ['TIKR_ACCOUNT_PASSWORD']
        
        browser = scraper_utils.create_driver()
        browser.get('https://app.tikr.com/login')
        browser.find_element(By.XPATH, '//input[@type="email"]').send_keys(username)
        browser.find_element(By.XPATH, '//input[@type="password"]').send_keys(password)
        browser.find_element(By.XPATH, '//button/span').click()
        while 'Welcome to TIKR' not in browser.page_source:
            time.sleep(5)
        browser.get('https://app.tikr.com/screener?sid=1')

        fetch_button = WebDriverWait(browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button/span[contains(text(), "Fetch Screen")]/..'))
        )
        # Make sure the button is visible on the screen.
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", fetch_button)
        time.sleep(1)  # small delay for the scroll to finish

        # Use JavaScript for clicks (avoids footer error)
        browser.execute_script("arguments[0].click();", fetch_button)

        time.sleep(5)

        access_token = ''
        try:
            for request in browser.requests:
                if 'api.tikr.com/fs' in request.url and request.method == 'POST':
                    response = json.loads(request.body)
                    print('[ * ] Successfully fetched access token')
                    access_token = response['auth']
                    with open('token.tmp', 'w') as f:
                        f.write(access_token)
        except Exception as err:
            print(err)
        
        browser.close()
        return access_token
    
    def get_est_data(access_token: str, headers: str, tid: int, cid: int, test_mode: int) -> any:
        if test_mode == 0:
            url = 'https://api.tikr.com/est'
            payload = json.dumps({
                "auth": access_token,
                "tid": tid,
                "cid": cid,
                "p": "1",
                "v": "v1"
            })
            response = requests.post(url, headers=headers, data=payload)
            return response.json()
        else:
            with open('./tests/AAPL_est.json', 'r') as f:
                return json.load(f)
    
    def get_tf_data(access_token: str, headers: str, tid: int, cid: int, test_mode: int) -> any:
        if test_mode == 0:
            url = 'https://api.tikr.com/tf'
            payload = json.dumps({
                "auth": access_token,
                "tid": tid,
                "cid": cid,
                "p": "1",
                "repid": 1,
                "v": "v1"
            })
            response = requests.post(url, headers=headers, data=payload)
            return response.json()
        else:
            with open('./tests/AAPL_tf.json', 'r') as f:
                return json.load(f)
    
    def get_dailyv2_data(access_token: str, headers: str, tid: int, cid: int, test_mode: int) -> any:
        if test_mode == 0:
            url = 'https://api.tikr.com/daily_v2'
            payload = json.dumps({
                "auth": access_token,
                "tid": tid,
                "cid": cid,
                "chd": "inc",
                "v": "v2"
            })
            response = requests.post(url, headers=headers, data=payload)
            return response.json()
        else:
            with open('./tests/AAPL_daily_v2.json', 'r') as f:
                return json.load(f)
    
    def get_last_quote_data(access_token: str, headers: str, tid: int, cid: int, test_mode: int) -> any:
        if test_mode == 0:
            url = 'https://api.tikr.com/lastquote_it'
            payload = json.dumps({
                "auth": access_token,
                "ids": [
                    {
                        "cid": cid,
                        "tid": tid
                    }
                ]
            })
            response = requests.post(url, headers=headers, data=payload)
            return response.json()
        else:
            with open('./tests/AAPL_lastquote_it.json', 'r') as f:
                return json.load(f)
    
    ################################################
    # Functions to extract specific data from dailyv2 response
    ################################################

    def get_period_end_dates(est_response) -> list:
        period_end_dates = {}
        dates = est_response.get('dates', [])
        for period in dates:
            fiscal_year = period.get('fiscalyear')
            if fiscal_year not in period_end_dates:
                try:
                    period_end_date = period.get('periodenddate')
                    date_obj = datetime.fromisoformat(period_end_date.replace("Z", ""))
                    period_end_dates[fiscal_year] = date_obj
                except ValueError:
                    continue
        return period_end_dates
    

    ################################################################
    # Extract December values from a given category and item name
    ################################################################

    def get_end_period_data_from(category: str, item_name: str, dailyv2_response, period_end_dates: list) -> dict:
        multiples = dailyv2_response.get('cTblDataObj', {}).get(category, [])
        items = next(
            (item for item in multiples if item.get('name') == item_name),
            None  # default value if not found
        )
        
        data = items.get("data", {})

        end_periods_values = {}
        current_year = datetime.now().year
        last_month_current_year = 0
        last_value_current_year = ''
        for k, v in data.items():
            # Parse the ISO date (removing the trailing Z)
            dt = datetime.fromisoformat(k.replace("Z", ""))
            year = dt.year
            
            if dt.year == current_year:
                if dt.month > last_month_current_year:
                    last_month_current_year = dt.month
                    last_value_current_year = v.get("v")
            else:
                period_end_date = period_end_dates.get(year)
                if period_end_date and dt.month == period_end_date.month:
                    end_periods_values[year] = v.get("v")

        # If we didn't find a December value for the current year, use the last available month
        if current_year not in end_periods_values and last_month_current_year > 0:
            end_periods_values[current_year] = last_value_current_year
        
        # Sort by year
        end_periods_values = dict(sorted(end_periods_values.items()))

        return end_periods_values
    
    def get_market_cap_data(dailyv2_response, period_end_dates: list) -> dict:
        return scraper_utils.get_end_period_data_from('Multiples', 'Market Cap (MM)', dailyv2_response, period_end_dates)
    
    def get_price_close_data(dailyv2_response, period_end_dates: list) -> dict:
        return scraper_utils.get_end_period_data_from('Street Targets', 'Price Close', dailyv2_response, period_end_dates)
    
    def get_TEV_data(dailyv2_response, period_end_dates: list) -> dict:
        return scraper_utils.get_end_period_data_from('Multiples', 'Total Enterprise Value (MM)', dailyv2_response, period_end_dates)

    ###############################################################
    # End of December extraction functions
    ###############################################################

    def normalize_label(label):
        if not isinstance(label, str):
            return ''
        
        # convert to lowercase
        label = label.lower()
        
        # remove special characters
        label = re.sub(r'[%&(),]', '', label)
        
        # replace spaces, slashes, and hyphens with underscores
        label = re.sub(r'[\s/-]+', '_', label)
        
        # remove multiple underscores and trim leading/trailing underscores
        label = re.sub(r'_+', '_', label).strip('_')
        
        return label
    
    def resolve_dataitem_id(statement_name, statement_name_index, statement_name_list, resdata_name_list, resdata_name_index, column_name, alias_name):
        search_terms = []
        if isinstance(alias_name, str) and alias_name:
            search_terms.append(alias_name)
        if column_name not in search_terms:
            search_terms.append(column_name)

        for term in search_terms:
            normalized = scraper_utils.normalize_label(term)
            if not normalized:
                continue
            item_id = statement_name_index.get(statement_name, {}).get(normalized)
            if item_id:
                return item_id
            item_id = resdata_name_index.get(normalized)
            if item_id:
                return item_id

        for term in search_terms:
            normalized = scraper_utils.normalize_label(term)
            if not normalized:
                continue
            for cand_norm, item_id, _ in statement_name_list.get(statement_name, []):
                if not cand_norm:
                    continue
                if normalized == cand_norm or normalized in cand_norm or cand_norm in normalized:
                    return item_id
            for cand_norm, item_id, _ in resdata_name_list:
                if not cand_norm:
                    continue
                if normalized == cand_norm or normalized in cand_norm or cand_norm in normalized:
                    return item_id
        return None

    def extract_value(resdata_map, line_map, item_id, period_key):
        if not item_id:
            return '', False
        line = line_map.get(item_id) or resdata_map.get(item_id)
        if not line:
            return '', False
        period_entry = line.get(period_key)
        if not isinstance(period_entry, dict):
            return '', False
        value = period_entry.get('v')
        if value == 1.11:
            return '', True
        if value in (None, '', 'NA'):
            return '', False
        try:
            return float(value), False
        except (TypeError, ValueError):
            return '', False
    
    def get_period_structure(response):
        periods = response.get('dates', [])
        if not periods:
            return [], {}

        # filter periods by years from the env var
        # we need to add 1 to include the current year
        # e.g. if we want 3 years of history, we need to include current year + 3 previous years
        # the current year will be taken as LTM
        years_mount = int(os.environ['TIKR_EXPORT_YEARS']) + 1
        actual_year = datetime.now().year
        years = [actual_year - i for i in range(years_mount)]

        period_lookup = {}
        cutted_periods = []
        for period in periods:
            value = period.get('value')
            calendar_year = period.get('calendaryear')
            if calendar_year in years:
                period_lookup[value] = period
                cutted_periods.append(period)
        
        period_keys = [period['value'] for period in cutted_periods]

        return period_keys, period_lookup

    def get_statement_mappings(tf_response, dailyv2_response, statements, period_end_dates):
        # Map the API response blocks to the statements we care about
        statement_indices = {
            'income_statement': 0,
            'balancesheet_statement': 1,
            'cashflow_statement': 2,
            'multiples_statement': 3,
        }

        statement_data = {}
        statement_name_index = {}
        statement_name_list = {}
        financials = tf_response.get('financials', [])

        # Extract and index lines for each statement (income, balance sheet, cash flow)
        for statement_name, index in statement_indices.items():
            lines = financials[index] if index < len(financials) else []
            line_map = {}
            name_index = {}
            names_list = []
            for line in lines:
                dataitemid = line.get('dataitemid')
                if not isinstance(dataitemid, int):
                    continue
                line_map[dataitemid] = line
                name = line.get('name', '')
                normalized = scraper_utils.normalize_label(name)
                if normalized and normalized not in name_index:
                    name_index[normalized] = dataitemid
                names_list.append((normalized, dataitemid, name))
            statement_data[statement_name] = line_map
            statement_name_index[statement_name] = name_index
            statement_name_list[statement_name] = names_list
        
        def get_multiples_map():
            # Extract and index the multiples from dailyv2 response
            multiples = dailyv2_response.get('cTblDataObj', {}).get('Multiples', [])

            multiple_map = {}
            name_index = {}
            names_list = []
            id = 0 # just a counter for lineorder if missing
            for multiple in multiples:
                if multiple.get('tikrdisplay') != '1':
                    continue

                name = multiple.get('name', '')
                normalized = scraper_utils.normalize_label(name)
                if normalized and normalized not in name_index:
                    name_index[normalized] = id
                
                # For multiples, we want to replace the data with December values
                december_date = scraper_utils.get_end_period_data_from('Multiples', name, dailyv2_response, period_end_dates)
                if december_date:
                    multiple['data'] = december_date
                multiple_map[id] = multiple
                names_list.append((normalized, id, name))
                id += 1
                
            statement_data['multiples_statement'] = multiple_map
            statement_name_index['multiples_statement'] = name_index
            statement_name_list['multiples_statement'] = names_list

        # Add multiples to the statement data for reference
        get_multiples_map()

        resdata_map = {}
        resdata_name_index = {}
        resdata_name_list = []
        for line in tf_response.get('resData', {}).values():
            if not isinstance(line, dict):
                continue
            dataitemid = line.get('dataitemid')
            if not isinstance(dataitemid, int):
                continue
            resdata_map[dataitemid] = line
            name = line.get('name', '')
            normalized = scraper_utils.normalize_label(name)
            if normalized and normalized not in resdata_name_index:
                resdata_name_index[normalized] = dataitemid
            resdata_name_list.append((normalized, dataitemid, name))
        
        statements_config = []
        for statement in statements:
            statement_name = statement['statement']
            resolved_keys = {}
            for column, alias in statement['keys'].items():
                if not alias:
                    resolved_keys[column] = ''
                    continue
                item_id = scraper_utils.resolve_dataitem_id(statement_name, statement_name_index, statement_name_list, resdata_name_list, resdata_name_index, column, alias)
                if item_id is None:
                    resolved_keys[column] = ''
                else:
                    resolved_keys[column] = item_id
            statements_config.append({
                'statement': statement_name,
                'keys': statement['keys'],
                'resolved_keys': resolved_keys,
            })

        return statement_data, resdata_map, statements_config