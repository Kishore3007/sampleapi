from models import JobApplicationData
from file_extractor import extract_pdf_text, extract_docx_text, extract_doc_text
from openai_integration import structure_application_data
from database import collection
import os, logging, json


MAX_RETRIES = 2  # Number of retries for file processing errors
# Configure logging
logger = logging.getLogger(__name__)

async def file_processor(filename: str, folder_path: str) -> dict:
    file_path = os.path.join(folder_path, filename)
    retries = 0

    if not os.path.isfile(file_path):
        return {"filename": filename, "error": "File does not exist"}

    supported_extensions = ['.pdf', '.docx', '.doc']
    if not filename.lower().endswith(tuple(supported_extensions)):
        return {"filename": filename, "error": "Unsupported file type"}

    while retries <= MAX_RETRIES:
        try:
            # Extract text based on file type
            if filename.lower().endswith('.pdf'):
                extracted_text = extract_pdf_text(file_path)
            elif filename.lower().endswith('.docx'):
                extracted_text = extract_docx_text(file_path)
            elif filename.lower().endswith('.doc'):
                extracted_text = extract_doc_text(file_path)
            else:
                continue

            # Structure the extracted text
            structured_data = structure_application_data(extracted_text)
            logger.info(f"Structured data prepared for file: {filename}")

            structured_data["resume title"] = filename


            # Store the structured data in MongoDB
            result = await collection.insert_one(structured_data)
            structured_data["_id"] = str(result.inserted_id)
            logger.info(f"Data inserted into MongoDB for file {filename} with ID: {result.inserted_id}")
            return structured_data

        except json.JSONDecodeError as e:
            retries += 1
            logger.error(f"JSON parsing error for file {filename}: {e}")
            if retries > MAX_RETRIES:
                return {"filename": filename, "error": "Max retries reached due to JSONDecodeError"}
        except Exception as e:
            retries += 1
            logger.error(f"Error processing file {filename}: {e}")
            if retries > MAX_RETRIES:
                return {"filename": filename, "error": f"Max retries reached due to {str(e)}"}
