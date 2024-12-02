import os
import openai
import json
from typing import List, Dict
from fastapi import HTTPException
from models import JobApplicationData

# Set up OpenAI API key
openai.api_key = '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'


# Function to clean the structured response by removing the JSON markers
def clean_json_output(response_text):
    if response_text.startswith("```json") and response_text.endswith("```"):
        response_text = response_text[7:-3].strip()
    return response_text

# Function to ensure fields are stored as lists
def ensure_list_fields(data, fields):
    for field in fields:
        if field in data and not isinstance(data[field], list):
            data[field] = [data[field]]
    return data

# Function to send extracted text to OpenAI API for structuring
def structure_application_data(extracted_text):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a job application reviewer."},
                {"role": "user", "content": f"""Extract and structure the job application text into a JSON object, following this exact format:

                {{
                    "name": "string",
                    "designation": [],
                    "contact number": [],
                    "email address": "string",
                    "education": [],
                    "current company name": "string",
                    "current location": "string",
                    "primary skills": [],
                    "secondary skills": [],
                    "total experience": int,
                    "relevant experience (primary)": (
                        "job history": [
                            "job title": "string",
                            "job company": "string",
                            "job description": "string",
                            ],
                        ),
                    "relevant experience (secondary)": (
                        "projects": [
                            "project name": "string",
                            "project company": "string",
                            "project description": "string",
                            ],
                        "certifications": [
                            "certificate title": "string",
                            "certification provider": "string",
                            ],
                        ),
                    applicant description: "string"
                    ],
                    ...
                }}

                The given document is a resume of an applicant. Check what the job title, such as project manager or ai developer, is of the person and categorize it as designation. Add multiple if needed.
                Store total experience in months. Calculate from information given if needed. If not mentioned, store it as 0.
                Make sure to categorize any skills that would help with the applicants designation under primary skills and and the rest under secondary skills.
                Group relevant work/job experience under 'relevant experience (primary)'. Add more if mentioned or necessary.
                Group any projects, certifications, hackathon experience, etc under 'relevant experience (secondary)'. Add the name of the company/client for project company or personal project if mentioned and null if not mentioned. Add more if necessary.
                Store the most recent job/work experience in current company name.
                Store the address as current location.
                Make a summary 150 word summary of the applicant and store it in applicant description.
                If any value is missing, store it as null.

                Resume text: {extracted_text}"""}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        print(response)
        structured_response = response.choices[0].message.content.strip()
        structured_response = clean_json_output(structured_response)
        # structured_response = (structured_response).lower()

        if structured_response:
            try:
                structured_data = json.loads(structured_response)
                
                # Define all fields that should always be lists
                fields_to_check = [
                    'designation',
                    'education',
                    'relevant experience (primary)',
                    'relevant experience (secondary)'
                ]

                # Ensure all fields in the list are stored as lists
                structured_data = ensure_list_fields(structured_data, fields_to_check)

                return structured_data
            except json.JSONDecodeError as json_error:
                raise HTTPException(status_code=500, detail=f"Error parsing JSON: {json_error}")
        else:
            raise HTTPException(status_code=500, detail="Empty response from OpenAI.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during API call: {e}")


async def get_skill_match_score(job_description: str, primary_skills: List[str], secondary_skills: List[str], name: str):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a job application reviewer."},
                {"role": "user", "content": f"""
                Following is a job description: {job_description}
                
                These are the primary skills of a candidate: {', '.join(primary_skills)}
                
                These are the secondary skills of a candidate: {', '.join(secondary_skills)}
                
                Check whether the primary and secondary skills of a candidate are suitable for a job based on the job description. Count the number of relevant primary skills and secondary skills.
                
                Save the suitable skills in matches.
                
                Give a JSON response in the following format:
                
                {{
                    "primary_count": int,
                    "secondary_count": int,
                    "matches": []
                    ...
                }}
                """}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        structured_response = response.choices[0].message.content.strip()
        structured_response = clean_json_output(structured_response)
        response_data = json.loads(structured_response)
        primary_count = response_data.get("primary_count", 0)
        secondary_count = response_data.get("secondary_count", 0)
        matches = response_data.get("matches", [])
        print("\n", name)
        print("\n", primary_count)
        print("\n", secondary_count)
        
        return {"primary_count": primary_count, "secondary_count": secondary_count, "matches": matches}
    
    except Exception as e:
        # raise HTTPException(status_code=500, detail=f"Error during API call: {e}")
        return 0.0, 0.0  # Fallback scores
