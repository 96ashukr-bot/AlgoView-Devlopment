# main/management/commands/dhan_instruments_update.py
from django.core.management.base import BaseCommand
import requests
import os
from datetime import datetime
from django.conf import settings

class Command(BaseCommand):
    help = "Updates Dhan trading instruments CSV files daily"

    def handle(self, *args, **options):
        try:
            # Define URLs and paths
            urls = {
                'compact': "https://images.dhan.co/api-data/api-scrip-master.csv",
                # 'detailed': "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
            }
            
            base_dir = os.path.join(settings.BASE_DIR, "main")
            
            for version, url in urls.items():
                filename = f"dhantoken.csv"
                filepath = os.path.join(base_dir, filename)
                
                # Download the file
                response = requests.get(url)
                response.raise_for_status()
                
                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully updated filename and there {version} instruments at {filepath}"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to update Dhan instruments: {str(e)}"
            ))
            raise e