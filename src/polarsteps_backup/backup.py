import time
import random
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Any, Mapping

from polarsteps_api.client import PolarstepsClient
from polarsteps_api.models.response import TripResponse
from polarsteps_api.models.trip import Trip

logger = logging.getLogger(__name__)

class PolarstepsBackup:
    """Backup a Polarsteps trip, including metadata and optional images."""
    TRIP_JSON_FILENAME = "trip.json"
    IMAGE_EXTENSION = ".jpg"
    TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
    S3_MEDIA_DOMAIN = "polarsteps.s3.amazonaws.com"
    POLARSTEP_MEDIA_DOMAIN = "media.prod.polarsteps.com"
    USER_AGENT = "PolarstepsBackup/1.0"

    def __init__(
        self,
        trip_id: str,
        backup_images: bool = False,
        backup_root: str | Path = "backups",
        media_download_delay: bool = True,
    ) -> None:
        """Initialize a Polarsteps backup instance."""
        self.trip_id = trip_id
        self.backup_images = backup_images
        self.backup_root = Path(backup_root)
        self.media_download_delay = media_download_delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.USER_AGENT,
                "Accept": "image/*",
            }
        )

    def backup_trip(self) -> None:
        """Fetch the trip data and save the backup locally."""
        client = PolarstepsClient()
        trip_response: TripResponse = client.get_trip(self.trip_id)

        trip: Trip | None = trip_response.trip
        if trip_response.is_error or trip is None:
            raise RuntimeError(f"Cannot fetch trip: {self.trip_id}")

        backup_dir = self._create_backup_dir(trip)

        logger.info("Backup trip name: %s", trip.slug)
        logger.info("Backup directory: %s", backup_dir)

        self._save_trip_json(trip, backup_dir)

        if not self.backup_images:
            return

        steps = trip_response.data.get("all_steps", [])
        for step in steps:
            self._backup_step_images(step, backup_dir)

    def _create_backup_dir(self, trip: Trip) -> Path:
        """Create and return the backup directory for the given trip."""
        backup_dir = self.backup_root / trip.slug / self._get_datetime()
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _save_trip_json(self, trip: Trip, backup_dir: Path) -> None:
        """Save the trip metadata as a JSON file."""
        trip_json = trip.model_dump_json(indent=4)
        output_path = backup_dir / self.TRIP_JSON_FILENAME
        with output_path.open("w", encoding="utf-8") as f:
            f.write(trip_json)
        
    def _get_datetime(self) -> str:
        """Return the current date and time as a compact timestamp string."""
        return datetime.now().strftime(self.TIMESTAMP_FORMAT)

    def _backup_step_images(self, step: Mapping[str, Any], backup_dir: Path) -> None:
        """Download and save all images for a single trip step."""
        step_id = step.get("id")
        step_name = step.get("name", "unknown-step")

        if step_id is None:
            logger.info("Skip step without id")
            return

        logger.info("Backup step name: %s", step_name)

        step_dir = backup_dir / str(step_id)
        step_dir.mkdir(parents=True, exist_ok=True)

        for media in step.get("media", []):
            media_id = media.get("id")
            is_image_deleted = media.get("is_deleted")

            if media_id is None:
                logger.info("Skip media without id")
                continue
            
            if is_image_deleted:
                logger.info("Skip media if the image has been deleted")
                return

            output_path = step_dir / f"{media_id}{self.IMAGE_EXTENSION}"

            self._apply_media_download_delay()
            success = self._download_image(media, output_path)

            if not success:
                logger.info("Cannot download image: %s", media_id)
                continue

    def _apply_media_download_delay(self) -> None:
        """Add a random delay between media downloads to avoid stressing the API."""

        if not self.media_download_delay:
            return
    
        delay = random.uniform(1.5, 5.0)
        logger.info(
            "Waiting %.2f seconds before downloading media image to avoid stressing the API",
            delay,
        )
        time.sleep(delay)


    def _download_image(self, media: Mapping[str, Any], output_path: Path) -> bool:
        """Download an image from a Polarsteps media object and save it to disk."""
        image_url = self._get_image_url(media)

        if image_url is None:
            return False

        logger.info("Downloading media image")

        try:
            response = self.session.get(
                url=image_url,
                stream=True,
                timeout=30,
            )

            if response.status_code == 429:
                logger.info("Too many requests. Slow down")
                return False

            response.raise_for_status()

            with output_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
            return True
        except requests.RequestException as error:
            logger.info("Download error: %s", error)
            return False

    def _get_image_url(self, media: Mapping[str, Any]) -> str | None:
        """Extract and normalize the image URL from a Polarsteps media object."""
        image_path = media.get("large_thumbnail_path")

        if not image_path:
            return None

        # The API returns an S3 media URL, but direct access to this URL fails.
        # Replacing it with the Polarsteps media domain makes the image publicly
        # downloadable, even without using the remember_token.
        # Note:
        # If authentication becomes required in the future, the remember_token
        # should be attached to the session header.
        return str(image_path).replace(
            self.S3_MEDIA_DOMAIN,
            self.POLARSTEP_MEDIA_DOMAIN,
        )
