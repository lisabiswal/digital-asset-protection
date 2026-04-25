import sqlite3
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Path to the bundled metadata database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "meta.db")

class DBManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_video_metadata(self, video_id: str) -> Optional[Dict]:
        """Fetches metadata for a single video ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"DB Error fetching video {video_id}: {e}")
            return None

    def list_all_videos(self) -> List[Dict]:
        """Lists all videos in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, duration, frame_count FROM videos")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"DB Error listing videos: {e}")
            return []

    def insert_video(self, video_data: Dict) -> bool:
        """Inserts a new video record (used during indexing)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO videos (id, title, youtube_url, thumbnail_url, duration, frame_count, faiss_start_idx, faiss_end_idx)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_data["id"], video_data["title"], video_data.get("youtube_url", ""),
                video_data.get("thumbnail_url", ""), video_data["duration"],
                video_data["frame_count"], video_data["faiss_start_idx"], video_data["faiss_end_idx"]
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Video {video_data['id']} already exists in database.")
            return False
        except Exception as e:
            logger.error(f"DB Error inserting video: {e}")
            return False

# Singleton instance
_db_manager = None

def get_db_manager():
    global _db_manager
    if _db_manager is None:
        _db_manager = DBManager()
    return _db_manager
