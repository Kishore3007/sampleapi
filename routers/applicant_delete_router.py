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

@router.delete("/delete-details")
async def delete_applicant_details(
    name: Optional[str] = Query(None, description="The name of the applicant"),
    email: Optional[str] = Query(None, description="The email address of the applicant")
):
    if not name and not email:
        raise HTTPException(status_code=400, detail="Please provide either a name or an email to delete the applicant.")

    query_filter = {}
    if name:
        query_filter["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive search for name
    if email:
        query_filter["email address"] = {"$regex": email, "$options": "i"}  # Case-insensitive search for email

    try:
        delete_result =  collection.delete_one(query_filter)

        if delete_result.deleted_count == 1:
            return {"detail": "Applicant successfully deleted."}
        else:
            raise HTTPException(status_code=404, detail="Applicant not found.")

    except Exception as e:
        logger.error(f"Error deleting applicant: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while deleting the applicant's details.")