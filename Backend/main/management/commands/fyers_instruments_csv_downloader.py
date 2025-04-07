# import requests
# import csv

# # Step 1: Download the JSON data
# url = "https://public.fyers.in/sym_details/NSE_FO_sym_master.json"
# response = requests.get(url)
# data = response.json()

# # Step 2: The data is a dictionary where keys are symbols
# # So let's convert it to a list of dictionaries
# symbols_dict = data
# symbols = []

# for symbol_name, symbol_data in symbols_dict.items():
#     # Add the symbol name as a key so we can use it in CSV
#     symbol_data["symbol"] = symbol_name
#     symbols.append(symbol_data)

# # Step 3: Inspect one entry to see available fields
# print("Sample fields:", symbols[0].keys())  # helpful during development

# # Step 4: Define the fields you want in the CSV
# fields = ["symbol", "symbolDetails", "optType", "strikePrice", "expiryDate", "minLotSize", "tickSize", "isin", "exchangeName"]

# # Step 5: Write to CSV
# with open("fyers_symbols.csv", "w", newline="", encoding="utf-8") as f:
#     writer = csv.DictWriter(f, fieldnames=fields)
#     writer.writeheader()
#     for symbol in symbols:
#         row = {field: symbol.get(field, "") for field in fields}
#         writer.writerow(row)

# print("✅ CSV file saved as 'fyers_symbols.csv'")


from django.core.management.base import BaseCommand
import requests
import csv
import os
import traceback
from django.conf import settings

class Command(BaseCommand):
    help = "Downloads and saves Fyers symbols CSV"

    def handle(self, *args, **options):
        try:
            url = "https://public.fyers.in/sym_details/NSE_FO_sym_master.json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            symbols = []
            for symbol_name, symbol_data in data.items():
                symbol_data["symbol"] = symbol_name
                symbols.append(symbol_data)

            fields = [
                "symbol", "symbolDetails", "optType", "strikePrice",
                "expiryDate", "minLotSize", "tickSize", "isin", "exchangeName"
            ]

            base_dir = os.path.join(settings.BASE_DIR, "main")
            os.makedirs(base_dir, exist_ok=True)
            filepath = os.path.join(base_dir, "fyers_symbols.csv")

            self.stdout.write(f"Saving to: {filepath}")

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for symbol in symbols:
                    row = {field: symbol.get(field, "") for field in fields}
                    writer.writerow(row)

            self.stdout.write(self.style.SUCCESS(
                f"✅ Fyers symbols saved to: {filepath}"
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed: {str(e)}"))
            self.stderr.write(traceback.format_exc())

