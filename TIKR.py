import argparse
import os

from tikr.DBUtils import create_database
from tikr.scraper import TIKR
from tikr.utils import bcolors

create_database()

def main():
    """Command line entry point for the scraper."""
    test_mode = os.environ.get('TIKR_TEST_MODE')

    if test_mode and test_mode == '1':
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
    print('[ . ] Done')


if __name__ == '__main__':
    main()
