import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

GCS_BUCKET = os.getenv("GCS_BUCKET")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

app = FastAPI(title="Digital Asset Protection API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize GCS Client
gcs_client = None
try:
    if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
        gcs_client = storage.Client(credentials=credentials)
        logger.info(f"GCS Client initialized with credentials from {GOOGLE_APPLICATION_CREDENTIALS}")
    else:
        # Fallback to default credentials (useful for Cloud Run)
        gcs_client = storage.Client()
        logger.info("GCS Client initialized with default credentials")
except Exception as e:
    logger.error(f"Failed to initialize GCS Client: {e}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gcs_initialized": gcs_client is not None,
        "bucket": GCS_BUCKET
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
