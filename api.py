"""
Flask API for Job Search Frontend
Serves job data from MongoDB with filtering capabilities
"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"error": str(e), "jobs": [], "total": 0}), 500

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = None
db = None
jobs_collection = None

if MONGODB_URI and "<db_password>" not in MONGODB_URI:
    try:
        client = MongoClient(MONGODB_URI)
        db = client.get_database("job_discovery")
        jobs_collection = db["jobs"]
        print("Connected to MongoDB Atlas")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

# Predefined roles from config
ROLES = [
    "Backend Engineer", "Frontend Engineer", "Full Stack Engineer", "Mobile Engineer",
    "Software Engineer", "Platform Engineer", "Systems Engineer", "Embedded Systems Engineer",
    "UI UX", "Cloud Engineer", "Cloud Architect", "DevOps Engineer", 
    "Site Reliability Engineer (SRE)", "Infrastructure Engineer", "Cloud Strategy Consultant",
    "Network Cloud Engineer", "Security Engineer", "Cloud Security Engineer",
    "Application Security Engineer", "Network Security Engineer", "Cyber Security Analyst",
    "GRC / Compliance Engineer", "IT Auditor", "FedRAMP / ATO Engineer",
    "Technology Risk Manager", "Data Engineer", "Data Scientist", "Analytics Engineer",
    "Business Intelligence Engineer", "Machine Learning Engineer", "AI Engineer",
    "Financial Analyst", "QA Engineer", "Automation Test Engineer", "Performance Test Engineer",
    "Security Test Engineer", "Test Lead / QA Lead", "IT Infrastructure Engineer",
    "IT Operations Engineer", "Linux / Unix Administrator", "Monitoring / SIEM Engineer",
    "Observability Engineer", "Release / Configuration Manager", "Network Engineer",
    "SAP Analyst", "ERP Consultant", "CRM Consultant", "ServiceNow Developer / Admin",
    "IT Asset / ITOM Engineer", "Workday Analyst", "Salesforce Developer",
    "Enterprise Architect", "Solutions Architect", "IT Manager", "CTO / CIO",
    "Product Manager", "Technical Product Manager", "Project Manager", "Program Manager",
    "Blockchain Engineer", "IoT Engineer", "Robotics Engineer", "AR / VR Engineer",
    "AML KYC", "Business Analyst"
]


@app.route('/api/roles', methods=['GET'])
def get_roles():
    """Get all available roles for autocomplete"""
    query = request.args.get('q', '').lower()
    if query:
        filtered = [r for r in ROLES if query in r.lower()]
        return jsonify(filtered[:10])  # Limit suggestions
    return jsonify(ROLES)


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get jobs with optional filters"""
    if jobs_collection is None:
        return jsonify({"error": "Database not connected", "jobs": [], "total": 0})
    
    # Parse query params
    role = request.args.get('role', '')
    experience = request.args.get('experience', '')
    date_filter = request.args.get('date', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    # Build query
    query = {}
    
    if role:
        query["$or"] = [
            {"title": {"$regex": role, "$options": "i"}},
            {"role": {"$regex": role, "$options": "i"}}
        ]
    
    if experience:
        # Map experience levels to common keywords
        exp_keywords = {
            "entry": ["entry", "junior", "associate", "0-2", "intern"],
            "mid": ["mid", "intermediate", "3-5", "2-5"],
            "senior": ["senior", "lead", "principal", "staff", "5+", "7+"]
        }
        if experience.lower() in exp_keywords:
            keywords = exp_keywords[experience.lower()]
            query["$or"] = query.get("$or", []) + [
                {"title": {"$regex": "|".join(keywords), "$options": "i"}},
                {"experience": {"$regex": "|".join(keywords), "$options": "i"}}
            ]
    
    if date_filter:
        days_map = {"7": 7, "30": 30, "90": 90}
        if date_filter in days_map:
            cutoff = datetime.utcnow() - timedelta(days=days_map[date_filter])
            query["scraped_at"] = {"$gte": cutoff}
    
    # Execute query
    try:
        total = jobs_collection.count_documents(query)
        jobs = list(jobs_collection.find(query)
                    .sort([("scraped_at", -1), ("_id", -1)])  # Stable sort with _id
                    .skip((page - 1) * limit)
                    .limit(limit))
        
        # Convert ObjectId to string
        for job in jobs:
            job["_id"] = str(job["_id"])
            if "scraped_at" in job and isinstance(job["scraped_at"], datetime):
                job["scraped_at"] = job["scraped_at"].isoformat()
        
        return jsonify({
            "jobs": jobs,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({"error": str(e), "jobs": [], "total": 0})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get job statistics"""
    if jobs_collection is None:
        return jsonify({"total": 0, "sources": {}})
    
    try:
        total = jobs_collection.count_documents({})
        
        # Group by source
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}}
        ]
        sources = {doc["_id"]: doc["count"] for doc in jobs_collection.aggregate(pipeline) if doc["_id"]}
        
        return jsonify({"total": total, "sources": sources})
    except Exception as e:
        return jsonify({"error": str(e), "total": 0, "sources": {}})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
