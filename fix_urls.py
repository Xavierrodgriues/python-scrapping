"""
Script to fix relative URLs in MongoDB job data.
Specifically fixes ZipRecruiter URLs that are stored without the base domain.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI or "<db_password>" in MONGODB_URI:
    print("Error: MONGODB_URI not configured properly")
    exit(1)

client = MongoClient(MONGODB_URI)
db = client.get_database("job_discovery")
jobs_collection = db["jobs"]

# URL prefixes for each source
URL_PREFIXES = {
    "ZipRecruiter": "https://www.ziprecruiter.com",
    "Indeed": "https://www.indeed.com",
    "LinkedIn": "https://www.linkedin.com",
    "Glassdoor": "https://www.glassdoor.com",
    "RemoteOK": "https://remoteok.com",
    "WeWorkRemotely": "https://weworkremotely.com",
}

def fix_urls():
    """Fix relative URLs by prepending the correct base domain."""
    fixed_count = 0
    
    for source, base_url in URL_PREFIXES.items():
        # Find jobs with relative URLs (starting with /)
        query = {
            "source": source,
            "url": {"$regex": r"^/", "$options": ""}  # URLs starting with /
        }
        
        jobs = jobs_collection.find(query)
        
        for job in jobs:
            old_url = job["url"]
            new_url = f"{base_url}{old_url}"
            
            jobs_collection.update_one(
                {"_id": job["_id"]},
                {"$set": {"url": new_url}}
            )
            print(f"Fixed: {old_url} -> {new_url}")
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} URLs total.")

if __name__ == "__main__":
    print("🔧 Fixing relative URLs in MongoDB...")
    fix_urls()
    print("Done!")
