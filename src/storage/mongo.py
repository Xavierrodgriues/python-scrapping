import os
import pymongo
from typing import List, Dict
from loguru import logger
from dotenv import load_dotenv

# Load env variables
load_dotenv()

class MongoWriter:
    def __init__(self, collection_name: str = "jobs"):
        self.uri = os.getenv("MONGODB_URI")
        if not self.uri or "<db_password>" in self.uri:
            logger.warning("MONGODB_URI not set or contains placeholder. MongoDB storage disabled.")
            self.client = None
            self.collection = None
            return

        try:
            self.client = pymongo.MongoClient(self.uri)
            # Default database
            self.db = self.client.get_database("job_discovery")
            self.collection = self.db[collection_name]
            
            # Create index on URL to ensure uniqueness
            self.collection.create_index("url", unique=True)
            logger.info("Connected to MongoDB Atlas.")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.collection = None

    def upsert_jobs(self, jobs: List[Dict]):
        if self.collection is None:
            return

        if not jobs:
            return
            
        count = 0
        for job in jobs:
            try:
                # Upsert based on URL
                filter_query = {"url": job.get("url")}
                update_query = {"$set": job}
                
                result = self.collection.update_one(filter_query, update_query, upsert=True)
                if result.upserted_id or result.modified_count > 0:
                    count += 1
            except Exception as e:
                logger.error(f"Failed to upsert job {job.get('title')}: {e}")
                
        if count > 0:
            logger.success(f"Upserted {count} jobs to MongoDB.")
        else:
            logger.info("No new or updated jobs for MongoDB.")
