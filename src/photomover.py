#!/usr/bin/env python
# encoding: utf-8

import os
import filecmp
import shutil
import re
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
import locale

# Setting locale to the 'local' value
locale.setlocale(locale.LC_ALL, '')

exiftool_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Image-ExifTool', 'exiftool')
EXIF_TOOL_BATCH_SIZE = 50

class ExifTool(object):
    """Used to run ExifTool from Python and keep it open"""

    sentinel = "{ready}"

    def __init__(self, executable=exiftool_location, verbose=False):
        self.executable = executable
        self.verbose = verbose

    def __enter__(self):
        self.process = subprocess.Popen(
            ['perl', self.executable, "-stay_open", "True", "-@", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write(b'-stay_open\nFalse\n')
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args).encode('utf-8'))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.rstrip(' \t\n\r').endswith(self.sentinel):
            increment = os.read(fd, 4096)
            if self.verbose:
                sys.stdout.write(increment.decode('utf-8'))
            output += increment.decode('utf-8')
        return output.rstrip(' \t\n\r')[:-len(self.sentinel)]

    def get_metadata(self, filepaths):
        args = ['-j', '-a', '-G']
        args += ['-time:all']
        args += ['-r']
        args += filepaths
        try:
            return json.loads(self.execute(*args))
        except ValueError:
            sys.stdout.write('No files to parse or invalid data\n')
            exit()

def parse_filename(filename):
    date_patterns = [
        (r'(\d{4}[-_]\d{2}[-_]\d{2})', lambda d: datetime.strptime(d, '%Y-%m-%d') if '-' in d else datetime.strptime(d, '%Y_%m_%d')),  # YYYY-MM-DD or YYYY_MM_DD
        (r'(\d{8})', lambda d: datetime.strptime(d, '%Y%m%d')),  # YYYYMMDD
        (r'(\d{4}[-_]\d{2}[-_]\d{2}[-_]\d{2}[-_]\d{2}[-_]\d{2})', lambda d: datetime.strptime(d, '%Y-%m-%d-%H-%M-%S') if '-' in d else datetime.strptime(d, '%Y_%m_%d_%H_%M_%S')),  # YYYY-MM-DD-HH-MM-SS or YYYY_MM_DD_HH_MM_SS
        (r'(\d{14})', lambda d: datetime.strptime(d, '%Y%m%d%H%M%S')),  # YYYYMMDDHHMMSS
        (r'(\d{8}_\d{6})', lambda d: datetime.strptime(d, '%Y%m%d_%H%M%S'))  # YYYYMMDD_HHMMSS
    ]
    
    for pattern, parser in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            try:
                return parser(date_str)
            except ValueError:
                continue
    return None

def resolve_duplicate(new_path, source_path, dry_run_history = None):
    base, extension = os.path.splitext(new_path)
    counter = 1
    while (dry_run_history and new_path in dry_run_history) or (not dry_run_history and os.path.exists(new_path)):
        ## compare files
        if dry_run_history:
            dest_compare = dry_run_history[new_path]  # Get the source for comparison, because dry-run mode doesnt change file-system
        else:
            dest_compare = new_path
        if filecmp.cmp(source_path, dest_compare):  # check for identical files
            return None

        new_path = f"{base}_{counter}{extension}"
        counter += 1
    return new_path

def get_date_taken(filepath):
    with ExifTool() as e:
        metadata = e.get_metadata(filepath)
        if metadata and len(metadata) > 0:
            date_tags = ['EXIF:DateTimeOriginal', 'QuickTime:CreateDate', 'QuickTime:CreationDate']
            metadata = metadata[0]
            for tag in date_tags:
                date_str = metadata.get(tag)
                if date_str:
                    try:
                        return validate_parsed_date(datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S'))
                    except ValueError:
                        return None
    return None

def validate_parsed_date(parsed_date):
    #TODO check if date is correct, > 1900 etc...
    return parsed_date

def log_ignored_file(file_path, log_file):
    with open(log_file, 'a') as log:
        log.write(file_path + '\n')

def organize_files(src_dir, dest_dir, dry_run=True, move=False, log_file='ignored_files.log', max_workers=1):
    # Clear the log file

    exif_batch_paths = []
    dry_run_history = {} if dry_run else None # destination to source map
    for root, dirs, files in os.walk(src_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            date_taken = parse_filename(filename)

            if not date_taken:
                exif_batch_paths.append(file_path)
                if len(exif_batch_paths) >= EXIF_TOOL_BATCH_SIZE:
                    dates_taken = get_date_taken_batch(exif_batch_paths)
                    for path, date in zip(exif_batch_paths, dates_taken):
                        process_file(path, date, dest_dir, dry_run, move, log_file, dry_run_history)
                    exif_batch_paths.clear()
                continue
            
            process_file(file_path, date_taken, dest_dir, dry_run, move, log_file, dry_run_history)
    
    # Process remaining files in the batch
    if exif_batch_paths:
        dates_taken = get_date_taken_batch(exif_batch_paths)
        for path, date in zip(exif_batch_paths, dates_taken):
            process_file(path, date, dest_dir, dry_run, move, log_file, dry_run_history)

def process_file(file_path, date_taken, dest_dir, dry_run, move, log_file, dry_run_history):
    if not date_taken:
        print(f"nodate {file_path}")
        log_ignored_file(file_path, log_file)
        return

    year = date_taken.strftime('%Y')
    month = date_taken.strftime('%m') + '-' + date_taken.strftime('%b').lower()
    new_dir = os.path.join(dest_dir, year, month)
    new_path = os.path.join(new_dir, os.path.basename(file_path))

    fixed_new_path = resolve_duplicate(new_path, file_path, dry_run_history)

    if not fixed_new_path:
        print(f"identical {file_path} to {new_path}")
        if move:
            os.remove(file_path)
    else:
        if not dry_run:
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
            if move:
                shutil.move(file_path, fixed_new_path)
            else:
                shutil.copy2(file_path, fixed_new_path)
        else:
            dry_run_history[fixed_new_path] = file_path
        print(f"{'move' if move else 'copy'} {file_path} to {fixed_new_path}")

def get_date_taken_batch(filepaths):
    dates_taken = []
    with ExifTool() as e:
        metadata_list = e.get_metadata(filepaths)
        for metadata in metadata_list:
            date_taken = None
            date_tags = ['EXIF:DateTimeOriginal', 'QuickTime:CreateDate', 'QuickTime:CreationDate']
            for tag in date_tags:
                date_str = metadata.get(tag)
                if date_str:
                    try:
                        date_taken = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        date_taken = None
                    if date_taken:
                        date_taken = validate_parsed_date(date_taken)
                        break
            dates_taken.append(date_taken)
    return dates_taken

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Organize photos and videos by year and month.")
    parser.add_argument("src_dir", help="Source directory containing photos and videos.")
    parser.add_argument("dest_dir", help="Destination directory for organized files.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes.")
    parser.add_argument("--move", action="store_true", help="Move files instead of copying.")
    parser.add_argument("--log-file", default='ignored_files.log', help="Log file to record ignored files.")

    args = parser.parse_args()
    
    organize_files(args.src_dir, args.dest_dir, dry_run=args.dry_run, move=args.move, log_file=args.log_file)
