# polarsteps-trip-backup
Polarsteps backup command-line application

# Run
## Locally
```bash
uv sync --dev && uv pip install -e .
uv run main.py
```

# In Docker
```bash
docker build -t polarsteps-trip-backup .
docker run --rm -e POLARSTEPS_REMEMBER_TOKEN="xxxx" -v "${PWD}\backups:/app/backups" polarsteps-trip-backup --trip-id 00000 --backup-images
```

# Credits
This project relies on remuzel/polarsteps-api, an unofficial Python wrapper around the Polarsteps APIs.

The API client and the approach used to retrieve Polarsteps trip data are based on this project. This repository extends that idea by providing a backup-oriented tool to export trip data and optionally download related images.

This project is not affiliated with, endorsed by, or connected to Polarsteps.