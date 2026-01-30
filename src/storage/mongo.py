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
            self.db = self.client.get_database("jobs_db")
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

    def save_job_links(self, jobs: List[Dict], role: str = "Unknown"):
        """
        Save jobs to the job_links collection with standardized format:
        - apply_url, company, country, experience, role, scrapedAt, source, title
        """
        if self.client is None:
            logger.warning("MongoDB client is None - storage disabled!")
            return

        if not jobs:
            logger.debug("No jobs to save to job_links")
            return

        from datetime import datetime, timezone
        
        # Get or create job_links collection
        job_links_collection = self.db["job_links"]
        job_links_collection.create_index("apply_url", unique=True)
        
        new_count = 0
        for job in jobs:
            try:
                # Map to standardized format
                doc = {
                    "apply_url": job.get("url") or job.get("apply_url"),
                    "company": job.get("company", "Unknown"),
                    "country": job.get("location", "United States"),
                    "experience": job.get("experience", "Not Specified"),
                    "role": role or job.get("category", "Unknown"),
                    "scrapedAt": datetime.now(timezone.utc),
                    "source": job.get("source", "Unknown"),
                    "title": job.get("title", "Unknown")
                }
                
                if not doc["apply_url"]:
                    continue
                    
                # Upsert based on apply_url
                result = job_links_collection.update_one(
                    {"apply_url": doc["apply_url"]},
                    {"$set": doc},
                    upsert=True
                )
                if result.upserted_id:
                    new_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to save job link: {e}")
        
        if new_count > 0:
            logger.success(f"Saved {new_count} new job links to job_links collection.")
        else:
            logger.info(f"All {len(jobs)} jobs already exist in job_links collection.")
