import argparse
import os
import shutil

from tikr.DBUtils import create_database
from tikr.scraper import TIKR
from tikr.utils import bcolors

create_database()

def main():
    """Command line entry point for the scraper."""
    test_mode = int(os.environ.get('TIKR_TEST_MODE'))
    edit_file = int(os.environ.get('TIKR_EDIT_FILE'))

    if test_mode == 1:
        print(f'[ ! ] {bcolors.WARNING}Running in TEST MODE{bcolors.ENDC}')
    else:
        test_mode = 0
        parser = argparse.ArgumentParser(
            description="Scrape TIKR financial statements to a data file",
        )
        parser.add_argument(
            "query",
            nargs="?",
            help="Company name or ticker symbol",
        )
        args = parser.parse_args()

        asset = args.query or input(
            f'{bcolors.WARNING}[...]{bcolors.ENDC} Please enter ticker symbol or company name: '
        )

    scraper = TIKR(test_mode)
    print(f'[ . ] TIKR Statements Scraper: {bcolors.OKGREEN}Ready{bcolors.ENDC}')
    if test_mode == 0:
        tid, cid = scraper.find_company_info(asset)
            
        if not (tid and cid):
            print(f'[ - ] {bcolors.FAIL}[Error]{bcolors.ENDC}: Could not find company')
            return
    else:
        asset = 'AAPL'
        tid, cid = 2590360, 24937  # Apple Inc.
    
    print(
        f'[ . ] {bcolors.OKGREEN}Found company{bcolors.ENDC}: {asset} '
        f'[Trading ID: {tid}] [Company ID: {cid}]'
    )
    print('[ . ] Starting scraping...')
    scraper.get_financials(asset, tid, cid)
    exported_files = scraper.export(asset)
    if exported_files:
        for path in exported_files:
            print(f'[ + ] {bcolors.OKGREEN}Exported{bcolors.ENDC}: {path}')
    else:
        print(f'[ - ] {bcolors.FAIL}No files exported{bcolors.ENDC}')
    
    if edit_file == 1:
        # Identificar la industria para saber que plantilla usar
        industry = scraper.get_industry(tid, cid)
        print(f'Identified industry: {industry}')
        plantilla = 'IDC'
        # Seleccionar plantilla según industria
        if ('Financial' in industry) or ('Bank' in industry) or ('Capital Markets' in industry) or ('Finance' in industry) or ('Insurance' in industry) or ('Mortgage' in industry):
            plantilla = 'Financiera'
            print(f'Using Financial Industry template because: ' + industry)
        elif ('REITs' in industry):
            plantilla = 'REITs'
            print(f'Using REITs Industry template because: ' + industry)
        
        print(f'Edit the Excel file')
        # Copiar plantilla a archivo temporal
        shutil.copy(f"plantillas/Plantilla_TIKR_{plantilla}.xlsx", f"plantillas/Plantilla_TIKR_{plantilla}_{asset}.xlsx")
        scraper.edit_excel_file(f"plantillas/Plantilla_TIKR_{plantilla}.xlsx", tid, cid)

    print('[ . ] Done')


if __name__ == '__main__':
    main()
