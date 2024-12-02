from fastapi import APIRouter, UploadFile, File, HTTPException
from models import JobApplicationData
from file_extractor import extract_pdf_text, extract_docx_text, extract_doc_text
from openai_integration import structure_application_data
import os, logging
from pymongo import MongoClient

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

uri = "mongodb://dev-aitento-db-instance:nIqkixodE1xgWEpALlCs5mwHKTx4OS0gdwX7EG6jxoQihjSlXLo5PN9NEEhEbdHdjImG0NpTVYfpACDb4olL9A==@dev-aitento-db-instance.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&maxIdleTimeMS=120000&appName=@dev-aitento-db-instance@"

client = MongoClient(uri)
database = client["job_applications"]
collection = database["applications"]

# API endpoint to process the uploaded file
@router.post("/extract-text")
async def process_file(file: UploadFile = File(...)):
    # Ensure the 'temp' directory exists
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Save the uploaded file temporarily
    file_path = f"{temp_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extract text based on file type
    if file.filename.lower().endswith('.pdf'):
        extracted_text = extract_pdf_text(file_path)
    elif file.filename.lower().endswith('.docx'):
        extracted_text = extract_docx_text(file_path)
    elif file.filename.lower().endswith('.doc'):
        extracted_text = extract_doc_text(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF, DOC, or DOCX file.")

    # Structure the extracted text
    structured_data = structure_application_data(extracted_text)

    structured_data["resume title"] = file.filename

    logger.info("Structured data prepared for MongoDB insertion: %s", structured_data)

    # Store the structured data in MongoDB
    try:
        result =  collection.insert_one(structured_data)
        structured_data["_id"] = str(result.inserted_id)  # Include the MongoDB ID in the response
        logger.info("Data inserted into MongoDB with ID: %s", result.inserted_id)
    except Exception as e:
        logger.error("Failed to store data in MongoDB: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to store data in MongoDB: {e}")

    return structured_data
