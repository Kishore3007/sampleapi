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
collection = database["applications"]

# API endpoint to retrieve a specific applicant's details by designation
@router.get("/applicant-designation")
async def search_designated_applicant(
    designation: Optional[str] = Query(None, description="The designation of the applicant")
):
    if not designation:
        raise HTTPException(status_code=400, detail="Please provide a designation to search.")

    # Create a case-insensitive query filter for designation
    query_filter = {"designation": {"$regex": designation, "$options": "i"}}  # Case-insensitive search for designation

    try:
        # Query the MongoDB collection for the applicant details
        applicant =  collection.find_one(query_filter)

        if applicant:
            # Convert the MongoDB ObjectId to a string for JSON compatibility
            applicant["_id"] = str(applicant["_id"])
            return applicant
        else:
            raise HTTPException(status_code=404, detail="Applicant not found.")

    except Exception as e:
        logger.error("Error retrieving applicant details: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred while fetching the applicant's details.")
