from .utils import scraper_utils as utils
from tikr.DBUtils import insert_or_update_data

from datetime import datetime
import json
import keys
import requests
import os
import pandas as pd


class TIKR:
    statements_config = []
    period_end_dates = {}

    def __init__(self, test_mode=0, production_mode=0):
        try:
            self.test_mode = test_mode
            self.production_mode = production_mode
        except KeyError:
            raise

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://app.tikr.com',
            'Referer': 'https://app.tikr.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        self.statements = keys.statements
        self.content = {
            'income_statement': [],
            'cashflow_statement': [],
            'balancesheet_statement': [],
        }
        if os.path.isfile('token.tmp'):
            with open('token.tmp', 'r') as f:
                self.access_token = f.read()
        else:
            self.access_token = ''


    def set_token(self, token: str):
        if self.production_mode == 0:
            print('[ - ] Production mode is not enabled; token be set later.')
            return
        self.access_token = token
    

    def find_company_info(self, ticker, userID):
        # 1. Replicación estricta de las Cabeceras HTTP (Headers)
        # Se han transpuesto literalmente los valores de la traza de red.
        headers = {
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            # 'Accept-Language': 'es-ES,es;q=0.6',
            'Connection': 'keep-alive',
            'Host': 'tjpay1dyt8-dsn.algolia.net',
            'Origin': 'https://app.tikr.com',
            'Referer': 'https://app.tikr.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-GPC': '1',
            # User-Agent actualizado a la versión real detectada en la traza
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'accept': 'application/json',
            # Corrección Crítica: El Content-Type reportado por la red es text/plain, no application/json
            'content-type': 'text/plain',
        }

        # 2. Configuración de la Carga Útil (Payload)
        # Se mantiene la estructura exacta de la traza. El índice "tikr-terminal-v1" SIGUE ACTIVO.
        payload_dict = {
            "requests": [
                {
                    "indexName": "tikr-terminal-v1",
                    "query": ticker,
                    "userToken": userID
                }
            ]
        }
        
        # Se serializa el diccionario a una cadena JSON sin espacios en blanco 
        # para evitar alterar el Content-Length (Mitchell, 2018).
        data = json.dumps(payload_dict, separators=(',', ':'))

        # 3. Construcción de la URL de Destino
        # Note el cambio en el subdominio: tjpay1dyt8-dsn.algolia.net (Previamente usaba -3)
        # Note el cambio en el endpoint: /1/indexes/*/queries (Previamente usaba /query)
        url = (
            'https://tjpay1dyt8-dsn.algolia.net/1/indexes/*/queries?'
            'x-algolia-agent=Algolia%20for%20JavaScript%20(5.52.1)%3B%20Lite%20(5.52.1)%3B%20Browser&'
            'x-algolia-api-key=d88ea2aa3c22293c96736f5ceb5bab4e&'
            'x-algolia-application-id=TJPAY1DYT8'
        )

        # 4. Ejecución de la Petición
        try:
            response = requests.post(url, headers=headers, data=data)
            
            # Validación de la respuesta
            response.raise_for_status() 
            
            datos_json = response.json()

            # 1. Acceso al nodo principal 'results' de manera segura
            lista_resultados = datos_json.get('results', [])
            
            if lista_resultados and len(lista_resultados) > 0:
                # 2. Aislamiento del primer diccionario dentro del arreglo 'results'
                nodo_primario = lista_resultados[0]
                
                # 3. Acceso seguro al sub-arreglo 'hits'
                hits = nodo_primario.get('hits', [])
                
                # 4. Evaluación de la existencia de registros válidos
                if hits and len(hits) > 0:
                    primer_registro = hits[0]
                    
                    # 5. Extracción de las variables de interés
                    tid = primer_registro.get('tradingitemid')
                    cid = primer_registro.get('companyid')
                    
                    return tid, cid
                    
            # Retorno por defecto en caso de estructura inválida o vacía
            return None, None
            
        except requests.exceptions.HTTPError as err_http:
            print(f"Error HTTP: {err_http}")
            print(f"Cuerpo de la respuesta: {response.text}")
        except Exception as e:
            print(f"Error general de ejecución: {e}")
    

    def get_financials(self, asset: str, tid: int, cid: int, with_actual_year_included: int):
        while True:
            tf_response = utils.get_tf_data(self.access_token, self.headers, tid, cid, self.test_mode)

            if 'dates' not in tf_response or 'financials' not in tf_response:
                if self.production_mode == 1:
                    print('[ - ] Invalid or expired token detected, cannot proceed in production mode.  Exiting.')
                    raise RuntimeError('Invalid or expired token.')
                
                print('[ + ] Generating Access Token...')
                self.access_token = utils.get_access_token()
            else:
                break
        
        print('[ + ] Successfully retrieved data from TIKR API')

        est_response = utils.get_est_data(self.access_token, self.headers, tid, cid, self.test_mode)
        self.period_end_dates = utils.get_period_end_dates(est_response)
        est_response = None  # Free memory

        dailyv2_response = utils.get_dailyv2_data(self.access_token, self.headers, tid, cid, self.test_mode)
        
        marketcap_data = utils.get_market_cap_data(dailyv2_response, self.period_end_dates)
        price_close_data = utils.get_price_close_data(dailyv2_response, self.period_end_dates)
        tev_data = utils.get_TEV_data(dailyv2_response, self.period_end_dates)

        # Reset previously cached content before loading new data
        self.content = {
            'income_statement': [],
            'cashflow_statement': [],
            'balancesheet_statement': [],
            'multiples_statement': [],
        }

        print('[ + ] Exporting data...')

        # get all period keys and mapping
        period_keys, period_lookup = utils.get_period_structure(tf_response, with_actual_year_included)
        if not period_keys or not period_lookup:
            print('[ - ] No periods found in the tf response data')
            return

        # get all statements data and and config and resdata map
        statement_data, resdata_map, self.statements_config = utils.get_statement_mappings(tf_response, dailyv2_response, self.statements, self.period_end_dates)

        resolved_key_lookup = {
            cfg['statement']: cfg['resolved_keys'] for cfg in self.statements_config
        }

        income_statement_map = statement_data.get('income_statement', {})

        # process each period and extract data
        for period_key in period_keys:
            period_info = period_lookup.get(period_key, {})
            year = period_info.get('calendaryear')
            for statement_cfg in self.statements_config:
                statement_name = statement_cfg['statement']
                line_map = statement_data.get(statement_name, {})
                resolved_keys = statement_cfg['resolved_keys']
                config_keys = statement_cfg['keys']
                data = {'company': asset, 'year': year}
                for column, alias in config_keys.items():
                    if column == 'free_cash_flow':
                        ops_id = resolved_keys.get('cash_from_operations')
                        capex_id = resolved_keys.get('capital_expenditure')
                        ops_value, ops_denied = utils.extract_value(resdata_map, line_map, ops_id, period_key)
                        capex_value, capex_denied = utils.extract_value(resdata_map, line_map, capex_id, period_key)
                        if ops_denied or capex_denied:
                            data[column] = ''
                        elif ops_value != '' and capex_value != '':
                            data[column] = ops_value + capex_value
                        else:
                            data[column] = ''
                        continue

                    if column == 'free_cash_flow_margins':
                        fcf = data.get('free_cash_flow')
                        revenue_id = resolved_key_lookup.get('income_statement', {}).get('revenues')
                        revenue_value, revenue_denied = utils.extract_value(resdata_map, income_statement_map, revenue_id, period_key)
                        if revenue_denied:
                            data[column] = ''
                        elif (
                            fcf not in (None, '')
                            and revenue_value not in ('', None)
                            and revenue_value != 0
                        ):
                            data[column] = (float(fcf) / float(revenue_value)) * 100
                        else:
                            data[column] = ''
                        continue

                    resolved_item_id = resolved_keys.get(column)
                    if not resolved_item_id:
                        data[column] = ''
                        continue
                    
                    if statement_name == 'multiples_statement':
                        # For multiples, resdata_map is in the line_map
                        multiple_resdata_map = line_map.get(resolved_item_id, {}).get('data')
                        if not multiple_resdata_map:
                            value, denied = '', True
                        else:
                            value = multiple_resdata_map.get(year, '')
                            denied = value == None or value == 1.11

                            if (alias in ['NTM Levered Free Cash Flow Yield', 'NTM Dividend Yield', 'LTM Dividend Yield']) and (value != '' and value != None):
                                try:
                                    value = value * 100
                                except (TypeError, ValueError):
                                    value = ''
                                    denied = True

                    else:
                        value, denied = utils.extract_value(resdata_map, line_map, resolved_item_id, period_key)
                    if denied:
                        data[column] = ''
                        continue

                    if value == '':
                        data[column] = ''
                        continue
                    
                    value = float(value)
                    value = round(value, 2,)
                    if column == 'income_tax_expense':
                        data[column] = value * -1
                    else:
                        data[column] = value
                
                if statement_name == 'income_statement':
                    # Add Market Cap, Price Close, and TEV data if available
                    if marketcap_data:
                        market_cap = marketcap_data.get(year, '')
                        data['market_cap'] = market_cap
                    else:
                        data['market_cap'] = ''

                    if price_close_data:
                        price_close = price_close_data.get(year, '')
                        data['price_close'] = price_close
                    else:
                        data['price_close'] = ''
                    
                    if tev_data:
                        tev = tev_data.get(year, '')
                        data['TEV'] = tev
                    else:
                        data['TEV'] = ''
                    
                self.content[statement_name].append(data)

        # Calculate additional metrics like YoY and Margins
        for statement in self.statements:
            statement_name = statement['statement']
            rows = self.content.get(statement_name, [])
            if not rows:
                continue

            yoy_columns = [column for column in statement['keys'] if 'yoy' in column]
            for idx, fiscalyear in enumerate(rows):
                for column in yoy_columns:
                    base_column = column.replace('_yoy', '')
                    if idx == 0:
                        fiscalyear[column] = ''
                        continue
                    current_value = rows[idx].get(base_column)
                    previous_value = rows[idx - 1].get(base_column)
                    if (
                        current_value not in ('', None)
                        and previous_value not in ('', None)
                        and previous_value != 0
                    ):
                        try:
                            fiscalyear[column] = round(
                                ((float(current_value) / float(previous_value)) - 1) * 100,
                                2,
                            )
                        except (TypeError, ValueError, ZeroDivisionError):
                            fiscalyear[column] = ''
                    else:
                        fiscalyear[column] = ''

            if statement_name == 'income_statement':
                margin_columns = {
                    'gross_profit_margin': ('gross_profit', 'revenues'),
                    'operating_margin': ('operating_income', 'revenues'),
                    'net_income_to_common_incl_extra_items_margins': (
                        'net_income_to_common_incl_extra_items',
                        'revenues',
                    ),
                    'net_income_to_common_excl_extra_items_margins': (
                        'net_income_to_common_excl_extra_items',
                        'revenues',
                    ),
                }
                for fiscalyear in rows:
                    for column, (numerator, denominator) in margin_columns.items():
                        num_val = fiscalyear.get(numerator)
                        denom_val = fiscalyear.get(denominator)
                        if (
                            num_val not in ('', None)
                            and denom_val not in ('', None)
                            and denom_val != 0
                        ):
                            try:
                                fiscalyear[column] = (float(num_val) / float(denom_val)) * 100
                            except (TypeError, ValueError, ZeroDivisionError):
                                fiscalyear[column] = ''
                        else:
                            fiscalyear[column] = ''

        # Almacena los datos en la DB
        self.export(asset, 'db')


    def get_industry(self, tid: int, cid: int):
        company_info = utils.get_tibobj_data(self.access_token, self.headers, tid, cid, self.test_mode)
        industry = company_info.get('data', {}).get('simpleindustrydescription', '')
        return industry


    def export(self, asset: str, export_format: str):
        export_format = export_format.lower()
        valid_formats = {'xlsx', 'csv', 'json', 'parquet', 'db'}
        if export_format not in valid_formats:
            print(f"[ - ] Unknown export format '{export_format}', defaulting to XLSX")
            export_format = 'xlsx'

        timestamp = datetime.now().strftime('%Y-%m-%d')
        base_filename = f"tests/results/{asset}_{timestamp}"
        base_name = os.path.splitext(base_filename)[0]

        if (export_format != 'db') :
            frames = {}
            for statement in self.statements:
                statement_name = statement['statement']
                rows = self.content.get(statement_name, [])
                if not rows:
                    continue
                columns = list(rows[0].keys())
                years = [row['year'] for row in rows]
                if years:
                    years[-1] = 'LTM'
                df = pd.DataFrame(rows, columns=columns, index=years)
                if 'year' in df.columns:
                    df = df.drop(columns='year')
                frames[statement_name] = df

            if not frames:
                print('[ - ] No data available to export')
                return []

            exported_files = []
            report_label = os.path.basename(base_name).split('_')[0]

        if export_format == 'xlsx':
            output_path = f"{base_name}.xlsx"
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                for statement_name, df in frames.items():
                    df_transposed = df.T
                    df_transposed.to_excel(writer, sheet_name=statement_name)

                    worksheet = writer.sheets[statement_name]
                    worksheet.write('A1', report_label)
                    for idx, _ in enumerate(df.columns):
                        width = 45 if idx == 0 else 15
                        worksheet.set_column(idx, idx, width)
            exported_files.append(output_path)

        elif export_format == 'csv':
            for statement_name, df in frames.items():
                df_out = df.T.reset_index().rename(columns={'index': 'Metric'})
                output_path = f"{base_name}_{statement_name}.csv"
                df_out.to_csv(output_path, index=False)
                exported_files.append(output_path)

        elif export_format == 'json':
            payload = {
                statement_name: df.T.to_dict(orient='index')
                for statement_name, df in frames.items()
            }
            return payload

        elif export_format == 'parquet':
            for statement_name, df in frames.items():
                df_out = df.T.reset_index().rename(columns={'index': 'Metric'})

                # Clean up empty strings & enforce numeric where possible
                df_out = df_out.replace('', pd.NA)
                df_out = df_out.convert_dtypes()
                for col in df_out.columns[1:]:
                    df_out[col] = pd.to_numeric(df_out[col], errors='coerce')

                output_path = f"{base_name}_{statement_name}.parquet"
                try:
                    df_out.to_parquet(output_path, index=False)
                except ImportError as err:
                    raise RuntimeError(
                        'Parquet export requires either pyarrow or fastparquet to be installed.'
                    ) from err
                exported_files.append(output_path)

        elif export_format == 'db':
            for statement in self.statements:
                statement_name = statement['statement']
                rows = self.content.get(statement_name, [])
                if not rows:
                    continue

                insert_or_update_data(statement_name, rows)
            print(f'[ + ] Data inserted into the database successfully.')
            exported_files = ['database']

        return exported_files


    def edit_excel_file(self, filepath: str, tid: int, cid: int, tipo_compania: str):
        """Apply formatting to the exported Excel file."""
        if not os.path.isfile(filepath):
            print(f'[ - ] File not found: {filepath}')
            return

        sheets_names = {
            'income_statement': '7.TIKR_IS',
            'balancesheet_statement': '8.TIKR_BS',
            'cashflow_statement': '9.TIKR_CF',
            'multiples_statement': '10.TIKR_Val',
        }

        sheets_titles = {
            'income_statement': 'Income Statement',
            'balancesheet_statement': 'Balance Sheet Statement',
            'cashflow_statement': 'Cash Flow Statement',
            'multiples_statement': 'Multiples',
        }

        last_quote = utils.get_last_quote_data(self.access_token, self.headers, tid, cid, self.test_mode)
        if last_quote:
            last_price = last_quote.get('last')[0].get('latestPrice', '')
            if last_price != '':
                last_price = round(float(last_price), 2)
        else:
            last_price = ''

        try:
            for statement in self.statements_config:
                statement_name = statement['statement']
                sheets_name = sheets_names.get(statement_name, statement_name)
                # Solo procesar multiples_statement para companias IDC
                if (statement_name == 'multiples_statement' and tipo_compania != 'IDC'):
                    continue

                rows = self.content.get(statement_name, [])

                if not rows:
                    print(f'[ - ] No data found for statement: {statement_name}')
                    return

                columns = []
                # Map columns using statements_config if available
                config_keys = statement.get('keys')
                for col in list(rows[0].keys()):
                    new_col = config_keys.get(col, col)
                    if (col == 'market_cap'):
                        new_col = 'Market Cap'
                    elif (col == 'price_close'):
                        new_col = 'Price Close'
                    elif (col == 'TEV'):
                        new_col = 'TEV'
                    elif (col == 'company'):
                        new_col = ''
                    elif (col == 'year'):
                        continue  # Skip 'year' column as it's used for index
                    columns.append(new_col)

                # Remove 'company' key and change the keys, by switching them with the values on statements_config for each row
                new_rows = []
                for row in rows:
                    new_row = {}
                    for key, value in row.items():
                        if (key == 'market_cap'):
                            new_row['Market Cap'] = value
                        elif (key == 'price_close'):
                            new_row['Price Close'] = value
                        elif (key == 'TEV'):
                            new_row['TEV'] = value
                        elif (key == 'company'):
                            new_row[''] = ''
                        else:
                            new_row[config_keys.get(key, key)] = value
                    new_rows.append(new_row)

                years = [row['year'] for row in new_rows]
                if years:
                    formatted_years = []
                    for i, y in enumerate(years):
                        if i == len(years) - 1:  # last item is LTM
                            formatted_years.append('LTM')
                        else:
                            if statement_name == 'multiples_statement':
                                december_date = '12/31/' + str(y-2000)
                                period_str = december_date
                            else:
                                end_period_date = self.period_end_dates.get(y, str(y))
                                period_str = end_period_date.strftime('%Y/%m/%d')
                            formatted_years.append(period_str)
                    years = formatted_years

                df = pd.DataFrame(new_rows, columns=columns, index=years)
                df_transposed = df.T

                # Cargar el workbook existente
                with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df_transposed.to_excel(writer, sheet_name=sheets_name)

                    worksheet = writer.sheets[sheets_name]
                    worksheet["A1"] = sheets_titles.get(statement_name, statement_name)

                    worksheet = writer.sheets['4.Valoracion']
                    if (tipo_compania == 'IDC'):
                        celda = "B19"
                    elif (tipo_compania == 'Financiera'):
                        celda = "D7"
                    else:
                        celda = "D8"
                    worksheet[celda] = last_price

                print(f'[ + ] Edited Excel file saved: {filepath}')

        except Exception as e:
            print(f'[ - ] Error editing Excel file: {e}')
