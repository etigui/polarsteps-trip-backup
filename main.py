import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from polarsteps_backup.backup import PolarstepsBackup

logger = logging.getLogger(__name__)

def init_logger() -> None:
    """Configure the application logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s %(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                "app.log",
                mode="a",
                encoding="utf-8",
            ),
        ],
    )

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the Polarsteps backup script."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Backup a Polarsteps trip",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--trip-id",
        type=int,
        required=True,
        help="Polarsteps trip ID to backup",
    )
    parser.add_argument(
        "--remember-token",
        default=os.getenv("POLARSTEPS_REMEMBER_TOKEN"),
        metavar="TOKEN",
        help=(
            "Polarsteps remember token. "
            "Defaults to the POLARSTEPS_REMEMBER_TOKEN environment variable."
        ),
    )
    parser.add_argument(
        "--backup-root",
        type=Path,
        default=Path("backups"),
        help="Root directory where the backup will be stored",
    )
    parser.add_argument(
        "--no-backup-media",
        action="store_false",
        dest="backup_media",
        help="Disable trip media downloads.",
    )
    parser.add_argument(
        "--no-media-download-delay",
        action="store_false",
        dest="media_download_delay",
        help="Disable the random delay (1.5 - 5 sec) between media image downloads.",
    )

    args = parser.parse_args()

    if not args.remember_token:
        parser.error(
            "A remember token is required. Provide --remember-token or set "
            "POLARSTEPS_REMEMBER_TOKEN in your environment or .env file."
        )
    return args

def main() -> None:
    """Run the Polarsteps backup command-line application."""
    init_logger()

    args = parse_args()

    ps_backup = PolarstepsBackup(
        trip_id =  args.trip_id,
        backup_root = args.backup_root,
        remember_token = args.remember_token,
        backup_media = args.backup_media,
        media_download_delay=args.media_download_delay,
    )
    try:
        ps_backup.backup_trip()
    except Exception:
        logger.exception("Backup failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
