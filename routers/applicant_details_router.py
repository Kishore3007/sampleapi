from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging
from pymongo import MongoClient

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

uri = "mongodb://dev-aitento-db-instance:nIqkixodE1xgWEpALlCs5mwHKTx4OS0gdwX7EG6jxoQihjSlXLo5PN9NEEhEbdHdjImG0NpTVYfpACDb4olL9A==@dev-aitento-db-instance.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&maxIdleTimeMS=120000&appName=@dev-aitento-db-instance@"

client = MongoClient(uri)
database = client["job_applications"]
hr_collection = database["applications"]

# API endpoint to retrieve a specific applicant's details by name or email
@router.get("/applicant-details")
async def get_applicant_details(
    name: Optional[str] = Query(None, description="The name of the applicant"),
    email: Optional[str] = Query(None, description="The email address of the applicant")
):
    if not name and not email:
        raise HTTPException(status_code=400, detail="Please provide either a name or an email to search.")

    # Create a case-insensitive query filter based on name or email
    query_filter = {}
    if name:
        query_filter["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive search for name
    if email:
        query_filter["email address"] = {"$regex": email, "$options": "i"}  # Case-insensitive search for email

    try:
        # Query the MongoDB collection for the applicant details
        applicant =  hr_collection.find_one(query_filter)

        if applicant:
            # Convert the MongoDB ObjectId to a string for JSON compatibility
            applicant["_id"] = str(applicant["_id"])
            return applicant
        else:
            raise HTTPException(status_code=404, detail="Applicant not found.")

    except Exception as e:
        logger.error("Error retrieving applicant details: %s", e)
        raise HTTPException(status_code=500, detail=e.__str__())