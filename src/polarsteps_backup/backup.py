import time
import random
import logging
import requests
from pathlib import Path
from enum import IntEnum
from datetime import datetime
from typing import Any, Mapping

from polarsteps_api.client import PolarstepsClient
from polarsteps_api.models.response import TripResponse
from polarsteps_api.models.trip import Trip

logger = logging.getLogger(__name__)

class MediaType(IntEnum):
    """Polarsteps Media type"""
    IMAGE = 0
    VIDEO = 1

class PolarstepsBackup:
    """Backup a Polarsteps trip, including metadata and optional images."""
    TRIP_JSON_FILENAME: str = "trip.json"
    IMAGE_EXTENSION: str = ".jpg"
    VIDEO_EXTENSION: str = ".mp4"
    TIMESTAMP_FORMAT: str = "%Y%m%d%H%M%S"
    S3_MEDIA_DOMAIN: str = "polarsteps.s3.amazonaws.com"
    POLARSTEP_MEDIA_DOMAIN: str = "media.prod.polarsteps.com"
    USER_AGENT: str = "PolarstepsClient/1.0"

    def __init__(
        self,
        trip_id: str,
        remember_token: str | None = None,
        backup_media: bool = True,
        backup_root: str | Path = "backups",
        media_download_delay: bool = True,
    ) -> None:
        """Initialize a Polarsteps backup instance."""
        self.trip_id = trip_id
        self.remember_token = remember_token
        self.backup_media = backup_media
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
        client = PolarstepsClient(
            remember_token = self.remember_token,
            cache_ttl = 1  # Keep cached values for only one second
        )
        trip_response: TripResponse = client.get_trip(self.trip_id)

        trip: Trip | None = trip_response.trip
        if trip_response.is_error:
            raise RuntimeError(f"Polarsteps API request failed. Check the URL and request headers, especially 'Polarsteps-Api-Version', which may no longer be valid.")
        if trip is None:
            raise RuntimeError(f"Cannot fetch trip: {self.trip_id}")

        backup_dir = self._create_backup_dir(trip)

        logger.info("Backup trip name: %s", trip.slug)
        logger.info("Backup directory: %s", backup_dir)

        self._save_trip_json(trip, backup_dir)

        if not self.backup_media:
            return

        steps = trip_response.data.get("steps", [])
        for step in steps:
            self._backup_step_media(step, backup_dir)

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

    def _backup_step_media(self, step: Mapping[str, Any], backup_dir: Path) -> None:
        """Download and save all images for a single trip step."""
        step_id = step.get("id")
        step_name = step.get("display_name", "drafting")

        if step_id is None:
            logger.info("Skip step without id")
            return

        logger.info("Backing up media for step: %s", step_name)

        step_dir = backup_dir / str(step_id)
        step_dir.mkdir(parents=True, exist_ok=True)

        for media in step.get("media", []):
            media_id = media.get("id")
            if media_id is None:
                logger.info("Skip media without id")
                continue
            
            if media.get("is_deleted"):
                logger.info("Skip image if it has been deleted")
                continue

            # Validate media type
            media_type = self._get_media_type(media)
            if media_type is None:
                logger.info("Skip unsupported media type: %s", media.get("type"))
                continue

            media_extension = self._get_media_extension(media_type)
            if media_extension is None:
                logger.info("Skip unsupported media extension")
                continue

            media_url = self._get_media_url(media, media_type)
            if media_url is None:
                logger.info("Skip unsupported media URL")
                continue

            output_path = step_dir / f"{media_id}{media_extension}"

            self._apply_media_download_delay()
            success = self._download_media(media_id, media_url, output_path)

            if not success:
                logger.info("Cannot download image: %s", media_id)
                continue

    def _apply_media_download_delay(self) -> None:
        """Add a random delay between media downloads to avoid stressing the API."""

        if not self.media_download_delay:
            return
    
        delay = random.uniform(1.5, 5.0)
        logger.info(
            "Waiting %.2f seconds before downloading image to avoid stressing the API",
            delay,
        )
        time.sleep(delay)

    def _download_media(self, media_id: int, media_url: str, output_path: Path) -> bool:
        """Download an image or video from a Polarsteps media object and save it to disk."""
        logger.info("Downloading media: %s", media_id)

        temp_path = output_path.with_suffix(output_path.suffix + ".part")

        try:
            with self.session.get(
                url=media_url,
                stream=True,
                timeout=(10, 120),
            ) as response:

                if response.status_code == 429:
                    logger.info("Too many requests. Slow down")
                    return False

                response.raise_for_status()

                with temp_path.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            f.write(chunk)

            temp_path.replace(output_path)
            return True

        except (requests.RequestException, OSError) as error:
            logger.info("Download error: %s", error)
            return False

        finally:
            temp_path.unlink(missing_ok=True)

    def _get_media_type(self, media: Mapping[str, Any]) -> MediaType | None:
        """Get the media type if supported."""
        try:
            return MediaType(media.get("type"))
        except (ValueError, TypeError):
            return None

    def _get_media_url(self, media: Mapping[str, Any], media_type: MediaType) -> str | None:
        """Get the download URL based on the media type."""

        # The API returns an S3 media URL, but direct access to this URL fails.
        # Replacing it with the Polarsteps media domain makes the image publicly
        # downloadable, even without using the remember_token.
        # Note:
        # If authentication becomes required in the future, the remember_token
        # should be attached to the session header.
        media_urls = {
            MediaType.IMAGE: str(media.get("large_thumbnail_path")).replace(
                self.S3_MEDIA_DOMAIN,
                self.POLARSTEP_MEDIA_DOMAIN,
            ),
            MediaType.VIDEO: media.get("path"),
        }
        return media_urls.get(media_type, None)

    def _get_media_extension(self, media_type: MediaType) -> str | None:
        """Get the media file extension based on the media type."""
        extensions = {
            MediaType.IMAGE: self.IMAGE_EXTENSION,
            MediaType.VIDEO: self.VIDEO_EXTENSION,
        }
        return extensions.get(media_type, None)
