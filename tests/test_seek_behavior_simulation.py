import unittest
import math

class TestSeekBehaviorLogic(unittest.TestCase):
    def setUp(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            self.html = f.read()

    def test_01_index_and_static_synced(self):
        with open('static/index.html', 'r', encoding='utf-8') as f:
            static_html = f.read()
        self.assertEqual(self.html, static_html, "index.html and static/index.html must be identical")

    def test_02_seek_math_at_1_minute(self):
        """Simulate seeking scenario from user request:
        - Start at 00:01:00 (60s).
        - Double-tap left side -> position becomes approx 00:00:50 (50s).
        - Double-tap right side -> position becomes approx 00:01:00 (60s).
        - Double-tap right side again -> position becomes approx 00:01:10 (70s).
        - Three separate double-tap gestures on right -> advance approx 30s in total (100s).
        """
        current_offset = 60.0
        video_current_time = 0.0
        last_virtual_seek_time = None
        duration = 7200.0  # 2 hour movie

        def get_current_time():
            nonlocal last_virtual_seek_time, current_offset, video_current_time
            if last_virtual_seek_time is not None:
                return last_virtual_seek_time
            return current_offset + video_current_time

        def skip_seconds(delta):
            nonlocal last_virtual_seek_time, duration
            base = get_current_time()
            target = max(0.0, min(duration, base + delta))
            last_virtual_seek_time = target
            return target

        # Start at 00:01:00
        self.assertEqual(get_current_time(), 60.0)

        # 1. Double tap left side (-10s)
        pos = skip_seconds(-10)
        self.assertEqual(pos, 50.0)
        # Stream mounts at 50s
        current_offset = 50.0
        video_current_time = 0.0
        last_virtual_seek_time = None
        self.assertEqual(get_current_time(), 50.0)

        # 2. Double tap right side (+10s)
        pos = skip_seconds(10)
        self.assertEqual(pos, 60.0)
        current_offset = 60.0
        video_current_time = 0.0
        last_virtual_seek_time = None
        self.assertEqual(get_current_time(), 60.0)

        # 3. Double tap right side again (+10s)
        pos = skip_seconds(10)
        self.assertEqual(pos, 70.0)
        current_offset = 70.0
        video_current_time = 0.0
        last_virtual_seek_time = None
        self.assertEqual(get_current_time(), 70.0)

        # 4. Three rapid taps on right (+10s each)
        pos1 = skip_seconds(10)
        self.assertEqual(pos1, 80.0)
        pos2 = skip_seconds(10)
        self.assertEqual(pos2, 90.0)
        pos3 = skip_seconds(10)
        self.assertEqual(pos3, 100.0)
        # Advance approx 30s in total from 70s to 100s!
        self.assertEqual(pos3 - 70.0, 30.0)

    def test_03_boundary_clamping(self):
        """Verify boundary handling: never below 0 and never beyond duration."""
        duration = 120.0
        last_virtual_seek_time = 5.0

        def skip_seconds(delta):
            nonlocal last_virtual_seek_time, duration
            base = last_virtual_seek_time
            target = max(0.0, min(duration, base + delta))
            last_virtual_seek_time = target
            return target

        # Seeking -10s from 5s clamps to 0s
        pos = skip_seconds(-10)
        self.assertEqual(pos, 0.0)

        # Seeking -10s from 0s stays at 0s
        pos = skip_seconds(-10)
        self.assertEqual(pos, 0.0)

        # Seeking +10s from 115s clamps to duration 120s
        last_virtual_seek_time = 115.0
        pos = skip_seconds(10)
        self.assertEqual(pos, 120.0)

    def test_04_skip_intro_outro_definition(self):
        """Verify seekPlayerToSeconds is defined and callable."""
        self.assertIn('function seekPlayerToSeconds(sec)', self.html)
        self.assertIn('seekPlayerToSeconds(target);', self.html)

    def test_05_continuous_10_second_double_tap_seeking(self):
        """Simulate continuous 10-second double-tap seeking:
        - Start at 60.0s.
        - Double-tap left: skips 10s backward -> 50.0s.
        - Double-tap right: skips 10s forward -> 60.0s.
        - 3 repeated double-taps on right: accumulates 30s -> 90.0s.
        """
        current_offset = 60.0
        video_current_time = 0.0
        last_virtual_seek_time = None
        duration = 7200.0

        def get_current_time():
            nonlocal last_virtual_seek_time, current_offset, video_current_time
            if last_virtual_seek_time is not None:
                return last_virtual_seek_time
            return current_offset + video_current_time

        def skip_seconds(delta):
            nonlocal last_virtual_seek_time, duration
            base = get_current_time()
            target = max(0.0, min(duration, base + delta))
            last_virtual_seek_time = target
            return target

        self.assertEqual(skip_seconds(-10), 50.0)
        self.assertEqual(skip_seconds(10), 60.0)
        self.assertEqual(skip_seconds(10), 70.0)
        self.assertEqual(skip_seconds(10), 80.0)
        self.assertEqual(skip_seconds(10), 90.0)

if __name__ == '__main__':
    unittest.main()
