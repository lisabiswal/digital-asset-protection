import os
import logging
from google.cloud import storage
from google.api_core import exceptions
from typing import Optional

logger = logging.getLogger(__name__)

class GCSManager:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = self._init_client()
        self.bucket = self.client.bucket(bucket_name) if self.client else None

    def _init_client(self):
        try:
            # Check for local key.json in the root of the project
            root_key = os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), "key.json"))
            if os.path.exists(root_key):
                logger.info(f"Using GCS credentials from {root_key}")
                return storage.Client.from_service_account_json(root_key)
            
            # Fallback to default credentials (GCP environment)
            return storage.Client()
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            return None

    def upload_video(self, local_path: str, upload_id: str) -> Optional[str]:
        """Uploads a local video file to GCS."""
        if not self.bucket:
            logger.warning("GCS bucket not initialized. Skipping upload.")
            return None

        try:
            blob_path = f"uploads/{upload_id}.mp4"
            blob = self.bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            
            gcs_uri = f"gs://{self.bucket_name}/{blob_path}"
            logger.info(f"Uploaded {local_path} to {gcs_uri}")
            return gcs_uri
        except exceptions.GoogleCloudError as e:
            logger.error(f"GCS upload error for {upload_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during GCS upload: {e}")
            return None

    def download_video(self, upload_id: str, destination_path: str) -> bool:
        """Downloads a video from GCS to a local path."""
        if not self.bucket:
            logger.warning("GCS bucket not initialized. Skipping download.")
            return False

        try:
            blob_path = f"uploads/{upload_id}.mp4"
            blob = self.bucket.blob(blob_path)
            blob.download_to_filename(destination_path)
            
            logger.info(f"Downloaded {blob_path} to {destination_path}")
            return True
        except exceptions.NotFound:
            logger.error(f"Video {upload_id} not found in GCS.")
            return False
        except exceptions.GoogleCloudError as e:
            logger.error(f"GCS download error for {upload_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during GCS download: {e}")
            return False

# Singleton instance for the app
_gcs_manager = None

def get_gcs_manager():
    global _gcs_manager
    if _gcs_manager is None:
        bucket_name = os.getenv("GCS_BUCKET", "sports-media-protection-bucket")
        _gcs_manager = GCSManager(bucket_name)
    return _gcs_manager
