# Photo and Video Organizer

This script organizes photos and videos by year and month. It can use filenames or EXIF metadata to determine the date the media was created.
It supports dry run, copy, and move modes.

## Features

- **Organize by Date**: Sorts files into directories by year and month.
- **EXIF Metadata Support**: Uses EXIF metadata to get the creation date if the filename does not contain it.
- **Duplicate Handling**: Resolves duplicate filenames by appending a counter.
- **Dry Run Mode**: Simulates the organization without making any changes.
- **Directory ignore**: Ignores folder names wherever they are in the tree
## Requirements

- Python 3.x
- `ExifTool`

## Usgage exemple with docker
```bash
docker run -v "/volume1/Photos:/photos:ro" -v "/volume1/Photos-sorted:/photos-sorted" photomover --dry-run /photos /photos-sorted --ignore-dirs @eaDir  --ignore-dirs "#recycle"
```
