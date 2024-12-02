from fastapi import APIRouter, Query, HTTPException
from models import JobApplicationData
from file_processor import file_processor
import os, logging
from concurrent.futures import ThreadPoolExecutor, as_completed


MAX_THREADS = 10  # Cap the number of threads

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()



# API endpoint to process multiple files in a folder with multithreading
@router.post("/extract-text-folder")
async def process_files_in_folder(
    folder_path: str = Query(..., description="The path to the folder containing the files"),
    num_threads: int = Query(5, description="Number of threads to use (max 10)")
):
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=400, detail="The provided folder path does not exist.")

    num_threads = min(max(num_threads, 1), MAX_THREADS)  # Cap threads between 1 and MAX_THREADS

    filenames = os.listdir(folder_path)
    results = []
    failed_files = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_file = {executor.submit(file_processor, filename, folder_path): filename for filename in filenames}

        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                result = await future.result()
                if "error" in result:
                    failed_files.append({"filename": filename, "error": result["error"]})
                else:
                    results.append(result)
            except Exception as e:
                logger.error(f"Unexpected error processing file {filename}: {e}")
                failed_files.append({"filename": filename, "error": str(e)})

    if not results and not failed_files:
        raise HTTPException(status_code=400, detail="No valid files were found or processed successfully in the folder.")

    response = {
        "processed_files": results,
        "failed_files": failed_files  # Return list of files that failed after retries
    }

    return response
