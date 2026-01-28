import pandas as pd
from typing import List, Dict
import os
from loguru import logger
from datetime import datetime

class JobWriter:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
    def save_jobs(self, jobs: List[Dict], filename_prefix: str = "jobs"):
        if not jobs:
            logger.warning("No jobs to save.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = pd.DataFrame(jobs)
        
        # Add timestamp column if not present
        if "scraped_at" not in df.columns:
            df["scraped_at"] = datetime.now().isoformat()
            
        # Deduplication based on URL if possible
        if "url" in df.columns:
            initial_count = len(df)
            df.drop_duplicates(subset=["url"], inplace=True)
            if len(df) < initial_count:
                logger.info(f"Removed {initial_count - len(df)} duplicate jobs.")

        # Save to CSV
        csv_path = os.path.join(self.data_dir, f"{filename_prefix}_{timestamp}.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {len(df)} jobs to {csv_path}")

        # Save to Excel
        xlsx_path = os.path.join(self.data_dir, f"{filename_prefix}_{timestamp}.xlsx")
        try:
            df.to_excel(xlsx_path, index=False)
            logger.info(f"Saved {len(df)} jobs to {xlsx_path}")
        except Exception as e:
            logger.error(f"Failed to save Excel: {e}")
