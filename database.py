from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
mongodb_uri = os.getenv('mongodb://dev-aitento-db-instance:nIqkixodE1xgWEpALlCs5mwHKTx4OS0gdwX7EG6jxoQihjSlXLo5PN9NEEhEbdHdjImG0NpTVYfpACDb4olL9A==@dev-aitento-db-instance.mongo.cosmos.azure.com:10255/?ssl=true&&connectTimeoutMS=30000&retrywrites=false&maxIdleTimeMS=120000&appName=@dev-aitento-db-instance@')
client = MongoClient(mongodb_uri)
db = client['job_applications']  # Database name
collection = db['applications']  # Collection name

def get_collection(database_name: str, collection_name: str = 'applications'):
    db = client[database_name]
    return db[collection_name]
