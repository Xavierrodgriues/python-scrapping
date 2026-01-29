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
            logger.warning("MongoDB collection is None - storage disabled!")
            return

        if not jobs:
            logger.debug("No jobs to upsert")
            return
        
        logger.debug(f"Attempting to upsert {len(jobs)} jobs to MongoDB")
        
        # Filter out jobs without valid URLs
        valid_jobs = [j for j in jobs if j.get("url")]
        if len(valid_jobs) < len(jobs):
            logger.warning(f"Filtered out {len(jobs) - len(valid_jobs)} jobs with missing URLs")
        
        new_count = 0
        updated_count = 0
        for job in valid_jobs:
            try:
                # Upsert based on URL
                filter_query = {"url": job.get("url")}
                update_query = {"$set": job}
                
                result = self.collection.update_one(filter_query, update_query, upsert=True)
                if result.upserted_id:
                    new_count += 1  # Truly new document
                elif result.modified_count > 0:
                    updated_count += 1  # Existing doc was updated
                # If neither, doc exists with same data (matched but not modified)
            except Exception as e:
                logger.error(f"Failed to upsert job {job.get('title')}: {e}")
                
        total = new_count + updated_count
        if total > 0:
            logger.success(f"Upserted {total} jobs to MongoDB ({new_count} new, {updated_count} updated).")
        else:
            logger.info(f"All {len(valid_jobs)} jobs already exist in MongoDB (no changes).")
