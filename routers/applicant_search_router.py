from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import re, logging
from pymongo import MongoClient

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


uri = "mongodb://dev-aitento-db-instance:nIqkixodE1xgWEpALlCs5mwHKTx4OS0gdwX7EG6jxoQihjSlXLo5PN9NEEhEbdHdjImG0NpTVYfpACDb4olL9A==@dev-aitento-db-instance.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&maxIdleTimeMS=120000&appName=@dev-aitento-db-instance@"

client = MongoClient(uri)
database = client["job_applications"]
collection = database["applications"]

@router.get("/search-by-skills")
async def search_by_skills(
    skills: Optional[List[str]] = Query(None, description="List of skills to search for"),
    years_of_experience: Optional[int] = Query(None, description="Years of experience to filter by"),
    location: Optional[str] = Query(None, description="Location to filter by"),
    display_fields: Optional[List[str]] = Query(
        default=["name", "designation", "contact number", "email address", "education",  "current company name",  "primary skills",  "secondary skills", "total experience", "current location", "score"],
        description="Fields to display (e.g., 'name', 'designation', 'email address')"
    ),
    store_scores: Optional[bool] = Query(False, description="Option to update the database with applicant scores")
):
    if not skills and years_of_experience is None and not location:
        raise HTTPException(status_code=400, detail="Please provide skills, years of experience, or location to search for.")

    # Create a query filter to search applicants
    query_filter = {}
    
    # If skills are provided, build a query for primary and secondary skills with case-insensitivity
    if skills:
        skill_regex = [re.compile(re.escape(skill), re.IGNORECASE) for skill in skills]
        query_filter["$or"] = [
            {"primary skills": {"$in": skill_regex}},
            {"secondary skills": {"$in": skill_regex}}
        ]

    # Add years of experience filter if provided
    if years_of_experience is not None:
        query_filter["total experience"] = {"$gte": years_of_experience * 12}  # Assuming total experience is in months

    # Add location filter if provided, using regex for partial matches and case-insensitivity
    if location:
        query_filter["current location"] = {"$regex": re.escape(location), "$options": "i"}  # Escape the location input for regex

    try:
        # Query MongoDB for all applicants
        cursor = collection.find({})
        all_applicants = await cursor.to_list(length=None)  # Fetch all applicants

        formatted_results = []
        for applicant in all_applicants:
            score = 0

            # Skill match scoring
            primary_skills = applicant.get("primary skills", [])
            secondary_skills = applicant.get("secondary skills", [])
            
            # Count matches for primary and secondary skills, with case insensitivity
            primary_skill_matches = sum(1 for skill in skills if any(re.search(re.escape(skill), ps, re.IGNORECASE) for ps in primary_skills)) if skills else 0
            secondary_skill_matches = sum(1 for skill in skills if any(re.search(re.escape(skill), ss, re.IGNORECASE) for ss in secondary_skills)) if skills else 0

            # Scoring based on skill matches
            score += primary_skill_matches * 10  # 5 points for each matched primary skill
            score += secondary_skill_matches * 5  # 2 points for each matched secondary skill

            # Experience scoring
            total_experience_months = applicant.get("total experience", 0)
            if years_of_experience is not None:
                required_experience_months = years_of_experience * 12
                if total_experience_months >= required_experience_months:
                    score += (total_experience_months / required_experience_months) / 5

            # Location match scoring
            current_location = applicant.get("current location")
            if location and current_location and re.search(re.escape(location), current_location, re.IGNORECASE):
                score += 1  # Increment for a location match

            # Create a base dictionary with applicant details
            applicant_details = {
                "name": applicant.get("name"),
                "designation": applicant.get("designation"),
                "contact number": applicant.get("contact number"),
                "email address": applicant.get("email address"),
                "education": applicant.get("education"),
                "current company": applicant.get("current company name"),
                "total experience": applicant.get("total experience") / 12,
                "current location": current_location,
                "score": score,
                "primary skills": applicant.get("primary skills"),
                "primary skills matched": primary_skill_matches,
                "work experience": applicant.get("relevant experience (primary)"),
                "secondary skills": applicant.get("secondary skills"),
                "secondary skill matches": secondary_skill_matches,
                "projects and certifications": applicant.get("relevant experience (secondary)")
            }

            # Filter results based on the display_fields provided by the user
            filtered_applicant = {field: applicant_details[field] for field in display_fields if field in applicant_details}
            formatted_results.append(filtered_applicant)

            # Optionally store the score in the database
            if store_scores:
                await collection.update_one({"_id": applicant["_id"]}, {"$set": {"score": score}})

        # Sort results by score in descending order
        formatted_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return formatted_results

    except Exception as e:
        logger.error(f"Error searching for applicants by skills: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while searching for applicants.")