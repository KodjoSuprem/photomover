from datetime import datetime
import re

date_patterns = [
   (r'[^0-9]*(\d{4}[-_]\d{2}[-_]\d{2}[-_]\d{2}[-_]\d{2}[-_]\d{2})[^0-9]*', lambda d: datetime.strptime(d, '%Y-%m-%d-%H-%M-%S') if '-' in d else datetime.strptime(d, '%Y_%m_%d_%H_%M_%S')),  # YYYY-MM-DD-HH-MM-SS or YYYY_MM_DD_HH_MM_SS

      (r'[^0-9]*(\d{8}_\d{6})[^0-9]*', lambda d: datetime.strptime(d, '%Y%m%d_%H%M%S')),  # YYYYMMDD_HHMMSS
       (r'[^0-9]*(\d{14})[^0-9]*', lambda d: datetime.strptime(d, '%Y%m%d%H%M%S')),  # YYYYMMDDHHMMSS
    (r'[^0-9]*(\d{4}[-_]\d{2}[-_]\d{2})[^0-9]*', lambda d: datetime.strptime(d, '%Y-%m-%d') if '-' in d else datetime.strptime(d, '%Y_%m_%d')),  # YYYY-MM-DD or YYYY_MM_DD
     
    (r'[^0-9]*(\d{8})[^0-9]', lambda d: datetime.strptime(d, '%Y%m%d')),  # YYYYMMDD

]

def parse_date_from_filename(filename):
    for pattern, parse_func in date_patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                return parse_func(match.group(1))
            except ValueError:
                continue
    return None

# Example usage
filenames = [
    "2023-05-15_photo.jpg",
    "20230515_event.png",
    "2023-05-15-14-30-00_snapshot.jpg",
    "20230515143000_capture.png",
    "20230515_143000_image.jpg",
    "wx_camera_1660062141481.jpg"
]

for filename in filenames:
    parsed_date = parse_date_from_filename(filename)
    if parsed_date:
        print(f"{filename}: {parsed_date}")
    else:
        print(f"{filename}: No valid date found")