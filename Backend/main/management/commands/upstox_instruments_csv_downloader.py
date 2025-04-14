# main/management/commands/upstox_instruments_csv_downloader.py
from django.core.management.base import BaseCommand
import requests
import pandas as pd
import gzip
import io
import os
from django.conf import settings
from datetime import datetime

class Command(BaseCommand):
    help = "Downloads and updates Upstox complete instruments CSV file"

    def handle(self, *args, **options):
        try:
            self.stdout.write(f"{datetime.now()} - Starting Upstox instruments CSV update...")
            
            # URL to the full compressed CSV file
            url = "https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz"
            
            # Download the .gz file
            response = requests.get(url)
            response.raise_for_status()
            self.stdout.write("Successfully downloaded the compressed CSV file")

            # Decompress and read CSV into DataFrame
            with gzip.open(io.BytesIO(response.content), mode='rt') as f:
                df = pd.read_csv(f)
            
            # Set file path
            base_dir = os.path.join(settings.BASE_DIR, "main")
            os.makedirs(base_dir, exist_ok=True)
            csv_path = os.path.join(base_dir, "complete.csv")

            # Save as regular CSV
            df.to_csv(csv_path, index=False)
            
            # Log some stats
            num_instruments = len(df)
            last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully updated Upstox instruments CSV at {csv_path}\n"
                f"Total instruments: {num_instruments:,}\n"
                f"Last updated: {last_updated}"
            ))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Failed to download CSV: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating Upstox symbols: {e}"))
