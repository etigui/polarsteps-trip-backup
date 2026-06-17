# Polarsteps Trip Backup
Polarsteps backup command-line application

## Run
### Locally
```bash
uv sync --dev && uv pip install -e .
uv run main.py
```

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

[!WARNING]\
> Your remember_token is a sensitive authentication credential. Do not share it, commit it to Git, or expose it publicly.

## Quick start
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


