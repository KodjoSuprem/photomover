import unittest
import os
import shutil
import filecmp
from datetime import datetime
from photomover import organize_files, parse_filename, resolve_duplicate, validate_parsed_date, get_date_taken_batch, ExifTool

class TestPhotomover(unittest.TestCase):

    def setUp(self):
        # Create temporary directories for testing
        self.test_dir = os.path.join(os.getcwd(), 'test_photomover')
        os.makedirs(self.test_dir, exist_ok=True)
        self.src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(self.src_dir, exist_ok=True)
        self.dest_dir = os.path.join(self.test_dir, 'dest')
        os.makedirs(self.dest_dir, exist_ok=True)

        # Create test files
        self.test_files = [
            ('2023-05-15_photo.jpg', '2023-05-15'),
            ('20230515_event.png', '2023-05-15'),
            ('2023-05-15-14-30-00_snapshot.jpg', '2023-05-15 14:30:00'),
            ('20230515143000_capture.png', '2023-05-15 14:30:00'),
            ('20230515_143000_image.jpg', '2023-05-15 14:30:00'),
            ('wx_camera_1660062141481.jpg', '2022-08-08 14:39:01'),  # Unix timestamp (milliseconds)
            ('20230515_duplicate.jpg', '2023-05-15'),
            ('20230515_duplicate_2.jpg', '2023-05-15'),
            ('no_date.txt', None),
            ('2023-05-15_duplicate_3.jpg', '2023-05-15'),
        ]
        for filename, date_str in self.test_files:
            filepath = os.path.join(self.src_dir, filename)
            with open(filepath, 'w') as f:
                f.write('test file')

    def tearDown(self):
        # Remove temporary directories
        shutil.rmtree(self.test_dir)

    def test_parse_filename(self):
        for filename, date_str in self.test_files:
            parsed_date = parse_filename(filename)
            if date_str:
                expected_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') if ' ' in date_str else datetime.strptime(date_str, '%Y-%m-%d')
                self.assertEqual(parsed_date, expected_date)
            else:
                self.assertIsNone(parsed_date)

    def test_resolve_duplicate(self):
        # Test with no duplicates
        self.assertEqual(resolve_duplicate(os.path.join(self.dest_dir, '2023', '05-May', '2023-05-15_photo.jpg'), os.path.join(self.src_dir, '2023-05-15_photo.jpg')), os.path.join(self.dest_dir, '2023', '05-May', '2023-05-15_photo.jpg'))

        # Test with duplicates
        self.assertEqual(resolve_duplicate(os.path.join(self.dest_dir, '2023', '05-May', '2023-05-15_photo.jpg'), os.path.join(self.src_dir, '2023-05-15_photo.jpg'), {'dest/2023/05-May/2023-05-15_photo.jpg': 'src/2023-05-15_photo.jpg'}), os.path.join(self.dest_dir, '2023', '05-May', '2023-05-15_photo_1.jpg'))
        self.assertEqual(resolve_duplicate(os.path.join(self.dest_dir, '2023', '05-May', '2023-05-15_photo_1.jpg'), os.path.join(self.src_dir, '2023-05-15_photo.jpg'), {'dest/2023/05-May/2023-05-15_photo.jpg': 'src/2023-05-15_photo.jpg', 'dest/2023/05-May/2023-05-15_photo_1.jpg': 'src/2023-05-15_photo.jpg'}), os.path.join(self.dest_dir, '2023', '05-May', '2023-05-15_photo_2.jpg'))

    def test_validate_parsed_date(self):
        self.assertIsNone(validate_parsed_date(datetime(1999, 1, 1)))
        self.assertIsNone(validate_parsed_date(datetime(2025, 1, 1)))
        self.assertEqual(validate_parsed_date(datetime(2023, 1, 1)), datetime(2023, 1, 1))

    def test_organize_files_dry_run(self):
        organize_files(self.src_dir, self.dest_dir, dry_run=True, move=False)
        self.assertEqual(stats['processed'], 9)
        self.assertEqual(stats['nodate'], 1)
        self.assertEqual(stats['duplicates'], 3)
        self.assertEqual(stats['renamed'], 1)

        # Check if files were copied (they shouldn't be in dry run)
        for filename, _ in self.test_files:
            src_path = os.path.join(self.src_dir, filename)
            dest_path = os.path.join(self.dest_dir, filename)
            self.assertTrue(os.path.exists(src_path))
            self.assertFalse(os.path.exists(dest_path))

    def test_organize_files_move(self):
        organize_files(self.src_dir, self.dest_dir, dry_run=False, move=True)
        self.assertEqual(stats['processed'], 9)
        self.assertEqual(stats['nodate'], 1)
        self.assertEqual(stats['duplicates'], 3)
        self.assertEqual(stats['renamed'], 1)

        # Check if files were moved
        for filename, _ in self.test_files:
            src_path = os.path.join(self.src_dir, filename)
            dest_path = os.path.join(self.dest_dir, filename)
            if filename == 'no_date.txt':
                self.assertTrue(os.path.exists(src_path))
                self.assertTrue(os.path.exists(dest_path))
            else:
                self.assertFalse(os.path.exists(src_path))
                self.assertTrue(os.path.exists(dest_path))

    def test_get_date_taken_batch(self):
        # Mock ExifTool for testing
        class MockExifTool:
            def get_metadata(self, filepaths):
                return [
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'QuickTime:CreateDate': '2023:05:15 14:30:00'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'QuickTime:CreationDate': '2022:08:08 14:39:01'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                    {'EXIF:DateTimeOriginal': '2023:05:15 14:30:00'},
                ]

        exiftool = MockExifTool()
        filepaths = [os.path.join(self.src_dir, f) for f, _ in self.test_files]
        dates_taken = get_date_taken_batch(filepaths, exiftool)
        expected_dates = [
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
            datetime(2022, 8, 8, 14, 39, 1),
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
            datetime(2023, 5, 15, 14, 30),
        ]
        self.assertEqual(dates_taken, expected_dates)

    def test_exiftool_integration(self):
        # This test requires ExifTool to be installed
        if not shutil.which('exiftool'):
            self.skipTest("ExifTool is not installed.")

        # Create a test image with a known date
        test_image_path = os.path.join(self.src_dir, 'test_image.jpg')
        subprocess.run(['exiftool', '-DateTimeOriginal=2023:05:15 14:30:00', test_image_path])

        # Get the date taken using ExifTool
        with ExifTool() as exiftool:
            metadata = exiftool.get_metadata([test_image_path])
            date_taken = datetime.strptime(metadata[0]['EXIF:DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')

        self.assertEqual(date_taken, datetime(2023, 5, 15, 14, 30))

if __name__ == '__main__':
    unittest.main()
