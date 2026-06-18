# Polarsteps Trip Backup
An unofficial Python tool to back up Polarsteps trips, including steps, locations, descriptions, and optional media downloads.

## Install and Run
### Locally
```bash
export POLARSTEPS_REMEMBER_TOKEN="<your-remember-token-here>
uv sync --dev && uv pip install -e .
uv run main.py --trip-id <your-trip-id-here>
```
> Step media images are not downloaded by default. Use `--backup-images` to include them in the backup.

### In Docker
```bash
docker build -t polarsteps-trip-backup .
docker run --rm -e POLARSTEPS_REMEMBER_TOKEN="<your-remember-token-here>" -v "${PWD}\backups:/app/backups" polarsteps-trip-backup --trip-id <your-trip-id-here> --backup-images
```

## Remember Token
This tool requires an authenticated Polarsteps session token. You must use your own Polarsteps account and only access trips or data that you are allowed to view.

To retrieve your authentication token:
1. Log in to Polarsteps from your web browser.
2. Open your browser developer tools.
    * Usually with F12
    * Or right click -> Inspect
3. Open the Application or Storage tab, depending on your browser.
4. Go to the Cookies section.
5. Find the cookie named `remember_token`.
6. Copy its value and provide it to the tool.

For example:
```bash
export POLARSTEPS_REMEMBER_TOKEN="<your-remember-token-here>"
```
> [!WARNING]\
> Your remember_token is a sensitive authentication credential. Do not share it, commit it to Git, or expose it publicly.

## Trip ID
Log in to Polarsteps from your web browser, then open the trip you want to back up.

The trip ID can be found in the trip URL:
```text
https://www.polarsteps.com/<username>/<trip-id>-<trip-name>
```
For example, in:
```text
https://www.polarsteps.com/johndoe/1234567-my-trip
```
the trip ID is `1234567`.

## Backup Structure
When a backup is created, the output is organized by trip name and backup date. This makes it possible to keep multiple backups of the same trip without overwriting previous ones.
```text
backup/
└── <trip-name>/
    └── <backup-datetime>/
        ├── trip.json
        ├── <step-id>/
        │   ├── <media-id>.jpeg
        │   └── <media-id>.jpeg
        └── <step-id>/
            ├── <media-id>.jpeg
            └── <media-id>.jpeg
```

The `trip.json` file contains the full trip data returned by Polarsteps, including the trip metadata, steps, locations, descriptions, and media references.

Each step is stored in a directory named after its Polarsteps step ID. If media backup is enabled, the images attached to that step are downloaded inside this directory.

Image files are named using their Polarsteps media ID:

```text
<media-id>.jpeg
```
This structure intentionally uses Polarsteps IDs instead of human-readable names. The goal is to keep the backup easy to process programmatically. By reading `trip.json`, it is possible to match each step directory with the corresponding step data, and each media file with the corresponding media entry.

In other words:
* `trip.json` is the source of truth for the trip structure.
* `<step-id>/` directories contain the media files for each step.
* `<media-id>.jpeg` files can be matched back to the media entries in `trip.json`.

This makes the backup more reliable and easier to restore, parse, or reuse in future tools.

## Quick Start
```pyhton
from polarsteps_backup.backup import PolarstepsBackup

ps_backup = PolarstepsBackup(
    trip_id =  "<your-trip-id-here>",
    backup_root = "backup",
    backup_images = True,
)
ps_backup.backup_trip()
```
> [!WARNING]\
> This project is **not affiliated with, endorsed by, or officially supported by Polarsteps**.
> 
> #### Terms of Use
> * **Personal backups only**: This tool is meant to help you back up your own Polarsteps trip data.
> * **Authentication required**: You must provide your own valid Polarsteps authentication cookie.
> * **Legitimate access only**: You should only use this tool with trips and data that belong to you, or that you are explicitly allowed to access.
> * **User responsibility**: You are responsible for ensuring that your use of this tool complies with Polarsteps' Terms of Service.
> * **No warranty**: This software is provided as-is, without any warranty or guarantee of availability, correctness, or continued functionality.
> 
> #### Risks and Limitations
> * Polarsteps may change, restrict, or remove their internal API endpoints at any time, which may break this tool without notice.
> * Because the API is undocumented, some data may be incomplete, unavailable, or returned in a different format.
> * Using unofficial API endpoints may violate Polarsteps' Terms of Service.
> * Excessive or automated usage may lead to rate limiting, blocking, account restrictions, or account suspension.
> * Authentication cookies are sensitive credentials and should never be shared, committed, or exposed publicly.
> 
> #### Responsible Use
> * Do not use this tool for commercial purposes.
> * Do not use it to access, scrape, or archive data that does not belong to you.
> * Do not run high-volume downloads or aggressive automated requests.
> * Respect Polarsteps' infrastructure and use reasonable delays between requests.
> 
> **By using this software, you acknowledge these limitations and agree to use it responsibly.**

## Credits
This project relies on [remuzel/polarsteps-api](https://github.com/remuzel/polarsteps-api/), an unofficial Python wrapper around the Polarsteps APIs.

The API client and the approach used to retrieve Polarsteps trip data are based on this project. This repository extends that idea by providing a backup-oriented tool to export trip data and optionally download related images.

This project is not affiliated with, endorsed by, or connected to Polarsteps.


