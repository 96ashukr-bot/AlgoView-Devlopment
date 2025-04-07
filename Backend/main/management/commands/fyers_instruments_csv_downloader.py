# main/management/commands/fyers_instruments_csv_downloader.py

from django.core.management.base import BaseCommand
import requests
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = "Downloads and updates Fyers instruments CSV file with proper column headers"

    def handle(self, *args, **options):
        try:
            url = "https://public.fyers.in/sym_details/NSE_FO.csv"
            response = requests.get(url)
            response.raise_for_status()

            decoded_content = response.content.decode('utf-8').splitlines()
            reader = csv.reader(decoded_content)
            rows = list(reader)

            if not rows:
                self.stdout.write(self.style.ERROR(" Empty CSV received from Fyers"))
                return

            #  Custom human-readable headers
            headers = [
                "FyToken", "Symbol Details", "Exchange Instrument Type", "Minimum Lot Size", "Tick Size", 
                "ISIN", "Trading Session", "Last Update Date", "Expiry Date", "Symbol Ticker", "Exchange", 
                "Segment", "Scrip Code", "Underlying Symbol", "Underlying Scrip Code", "Strike Price", 
                "Option Type", "Underlying FyToken", "Reserved 1", "Reserved 2", "Reserved 3"
            ]

            # Remove the original headers from the data
            data_rows = rows[1:]

            # Set file path
            base_dir = os.path.join(settings.BASE_DIR, "main")
            os.makedirs(base_dir, exist_ok=True)
            csv_path = os.path.join(base_dir, "fyers_instrument_symbol.csv")

            # Write to CSV
            with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data_rows)

            self.stdout.write(self.style.SUCCESS(f" Fyers symbols updated and saved at {csv_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f" Error updating Fyers symbols: {e}"))
