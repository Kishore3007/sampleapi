import re
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from database import  get_collection
import logging
from openai_integration import get_skill_match_score
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


uri = "mongodb://dev-aitento-db-instance:nIqkixodE1xgWEpALlCs5mwHKTx4OS0gdwX7EG6jxoQihjSlXLo5PN9NEEhEbdHdjImG0NpTVYfpACDb4olL9A==@dev-aitento-db-instance.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&maxIdleTimeMS=120000&appName=@dev-aitento-db-instance@"

client = MongoClient(uri)
database = client["job_applications"]
collection = database["applications"]

@router.get("/match-applicants-by-job-description")
async def match_applicants_by_job_description(
    job_description: str = Query(..., description="Job description to find matching applicants"),
    display_fields: Optional[List[str]] = Query(
        default=["name", "designation", "contact number", "email address", "education", "current company name", "primary skills", "secondary skills", "total experience", "current location", "score", "projects and certifications"],
        description="Fields to display (e.g., 'name', 'designation', 'email address')"
    ),
    prioritization_factors: Optional[List[str]] = Query(
        default=["skills"],
        description="Factors to prioritize (e.g., 'skills', 'location', 'years of experience')"
    ),
    location: Optional[str] = Query(None, description="Location to filter by"),
    required_experience_years: Optional[int] = Query(..., description="Required years of experience"),
    save_scores: bool = Query(False, description="Option to save scores in the database"),
    new_database_name: Optional[str] = Query(None, description="Name of the new database to store scores"),
    num_threads: int = Query(5, description="Number of threads to use (max 10)")
):
    num_threads = min(max(num_threads, 1), 10)

    try:
        # Connect to the new database if save_scores is enabled
        if save_scores and new_database_name:
            new_collection = collection = database["applicants_scores"]

        all_applicants =  collection.find().to_list(length=None)
        formatted_results = []

        async def process_applicant(applicant):
            primary_skills = applicant.get('primary skills', [])
            secondary_skills = applicant.get('secondary skills', [])
            current_location = applicant.get('current location')
            total_experience_years = applicant.get('total experience', 0) / 12
            name = applicant.get('name')

            skill_data = await get_skill_match_score(job_description, primary_skills, secondary_skills, name)
            primary_score = skill_data["primary_count"]
            secondary_score = skill_data["secondary_count"]
            matches = skill_data["matches"]

            location_match = bool(location and re.search(rf'\b{re.escape(location)}\b', current_location, re.IGNORECASE))
            experience_match = (total_experience_years - required_experience_years)

            skills_weight = 2
            experience_weight = 0.5
            higher_weight = 10
            if "skills" in prioritization_factors:
                skills_weight *= higher_weight
            if "years of experience" in prioritization_factors:
                experience_weight *= higher_weight

            score = (
                (primary_score * skills_weight) +
                (secondary_score * skills_weight / 2) +
                (experience_match * experience_weight)
            )

            applicant_data = {
                "name": name,
                "designation": applicant.get("designation"),
                "contact number": applicant.get("contact number"),
                "email address": applicant.get("email address"),
                "education": applicant.get("education"),
                "current company": applicant.get("current company name"),
                "total experience": total_experience_years,
                "current location": current_location,
                "score": score,
                "matches": matches,
                "primary skills": primary_skills,
                "secondary skills": secondary_skills,
                "location": location_match,
                "work experience": applicant.get("relevant experience (primary)"),
                "projects and certifications": applicant.get("relevant experience (secondary)"),
                "resume": applicant.get("resume title")
            }

            if save_scores and new_database_name:
                try:
                    await new_collection.update_one(
                        {"_id": applicant["_id"]},
                        {"$set": applicant_data},
                        upsert=True
                    )
                except Exception as e:
                    logger.error(f"Error updating score for applicant {applicant.get('name')}: {e}")

            return applicant_data

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_applicant = {executor.submit(process_applicant, applicant): applicant for applicant in all_applicants}

            for future in as_completed(future_to_applicant):
                applicant = future_to_applicant[future]
                try:
                    result = await future.result()
                    if result is not None:
                        filtered_data = {key: value for key, value in result.items() if key in display_fields}
                        formatted_results.append(filtered_data)
                except Exception as e:
                    logger.error(f"Unexpected error processing applicant {applicant.get('name')}: {e}")

        # Sort by location match (True first) and then by score in descending order
        formatted_results.sort(key=lambda x: (x.get("location_match", False), x.get("score", 0)), reverse=True)

        return formatted_results

    except Exception as e:
        logger.error(f"Error processing applicants: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while matching applicants.")
