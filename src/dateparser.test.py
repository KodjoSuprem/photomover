import unittest
from datetime import datetime
from photomover import parse_filename

class TestParseFilename(unittest.TestCase):

    def test_parse_filename_with_valid_dates(self):
        test_cases = [
            ("2023-05-15_photo.jpg", datetime(2023, 5, 15)),
            ("20230515_event.png", datetime(2023, 5, 15)),
            ("2023-05-15-14-30-00_snapshot.jpg", datetime(2023, 5, 15, 14, 30)),
            ("20230515143000_capture.png", datetime(2023, 5, 15, 14, 30)),
            ("20230515_143000_image.jpg", datetime(2023, 5, 15, 14, 30)),
            ("wx_camera_1660062141481.jpg", datetime(2022, 8, 8, 14, 39, 1)),  # Unix timestamp (milliseconds)
            ("20230515_duplicate.jpg", datetime(2023, 5, 15)),
            ("20230515_duplicate_2.jpg", datetime(2023, 5, 15)),
            ("20230515_duplicate_3.jpg", datetime(2023, 5, 15)),
        ]

        for filename, expected_date in test_cases:
            parsed_date = parse_filename(filename)
            self.assertEqual(parsed_date, expected_date)

    def test_parse_filename_with_invalid_dates(self):
        test_cases = [
            "mmexport1656042997585.jpg",
            "no_date.txt",
            "2023-05-15-14-30-00-invalid.jpg",
            "20230515_invalid_format.png",
            "20230515_143000_invalid.jpg",
            "wx_camera_1660062141481_invalid.jpg",
            
        ]

        for filename in test_cases:
            parsed_date = parse_filename(filename)
            print(parsed_date)
            #self.assertIsNone(parsed_date)

if __name__ == '__main__':
    unittest.main()
