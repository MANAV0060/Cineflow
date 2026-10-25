import unittest
import re

class TestMobileDoubleTapSeeking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('index.html', 'r', encoding='utf-8') as f:
            cls.html = f.read()
        with open('static/index.html', 'r', encoding='utf-8') as f:
            cls.static_html = f.read()

    def test_01_index_and_static_html_identical(self):
        """Ensure index.html and static/index.html are completely in sync."""
        self.assertEqual(self.html, self.static_html, "index.html and static/index.html must be identical")

    def test_02_touch_manipulation_on_click_surface(self):
        """Ensure video-click-surface has touch-action: manipulation to eliminate double-tap zoom delay."""
        match = re.search(r'id="video-click-surface"[^>]+>', self.html)
        self.assertIsNotNone(match, "video-click-surface element must exist")
        surface_tag = match.group(0)
        self.assertIn('touch-manipulation', surface_tag, "Should have touch-manipulation CSS class")
        self.assertIn('touch-action: manipulation', surface_tag, "Should have inline touch-action: manipulation style")

    def test_03_double_tap_timing_synchronization(self):
        """Verify double-tap window and single-tap delay are synchronized to prevent HUD blink."""
        self.assertIn('const DOUBLE_TAP_WINDOW = 300;', self.html)
        self.assertIn('const MAX_DOUBLE_TAP_DIST = 65;', self.html)
        self.assertIn('singleTapTimer = setTimeout(executeSingleTap, DOUBLE_TAP_WINDOW);', self.html)

    def test_04_single_tap_immediate_cancellation(self):
        """Verify singleTapTimer is canceled before execution when double-tap is registered."""
        self.assertIn('if (singleTapTimer) {', self.html)
        self.assertIn('clearTimeout(singleTapTimer);', self.html)
        self.assertIn('singleTapTimer = null;', self.html)

    def test_05_hud_visibility_preservation_on_seek(self):
        """Verify that double-tap does not force show/hide HUD, preserving current state."""
        # When HUD is visible, it resets the auto-hide timer to keep controls visible
        self.assertIn('if (isHudVisible) {\n            resetHudTimeout();\n          }', self.html)
        # Center controls are not hidden during active seek operations
        self.assertIn('if (loading && !isSeekingOperation) {', self.html)

    def test_06_center_pulse_suppressed_on_double_tap(self):
        """Verify skipSeconds supports suppressPulse so center pulse does not compete with double-tap arcs."""
        self.assertIn('function skipSeconds(delta, suppressPulse = false)', self.html)
        self.assertIn('if (!suppressPulse) {', self.html)
        self.assertIn("showPulse(delta > 0 ? 'forward_10' : 'replay_10');", self.html)
        self.assertIn("skipSeconds(side === 'left' ? -10 : 10, true);", self.html)

    def test_07_repeated_multi_tap_accumulation(self):
        """Verify multi-tap accumulation logic (+10s, +20s, +30s) and timer reset."""
        self.assertIn('if (isSeekingActive && lastTapSide === side) {', self.html)
        self.assertIn('accumulatedSeconds += 10;', self.html)
        self.assertIn('showDoubleTapFeedback(side, accumulatedSeconds);', self.html)
        self.assertIn('isSeekingActive = true;', self.html)
        self.assertIn('isSeekingActive = false;', self.html)

    def test_08_double_tap_feedback_badges_and_animation(self):
        """Verify feedback badges for left and right with animation re-trigger."""
        self.assertIn('id="double-tap-left"', self.html)
        self.assertIn('id="double-tap-right"', self.html)
        self.assertIn('id="double-tap-left-label"', self.html)
        self.assertIn('id="double-tap-right-label"', self.html)
        self.assertIn('void badge.offsetWidth;', self.html)

    def test_09_fullscreen_and_orientation_zone_geometry(self):
        """Verify relative coordinate calculation using getBoundingClientRect."""
        self.assertIn('const rect = surface.getBoundingClientRect();', self.html)
        self.assertIn('const relX = touch.clientX - rect.left;', self.html)
        self.assertIn('relX < width * 0.40', self.html)
        self.assertIn('relX > width * 0.60', self.html)

    def test_10_touch_and_ghost_click_safety(self):
        """Verify touch event handling, drag rejection, and ghost click suppression."""
        self.assertIn("surface.addEventListener('touchstart'", self.html)
        self.assertIn("surface.addEventListener('touchmove'", self.html)
        self.assertIn("surface.addEventListener('touchend'", self.html)
        self.assertIn("surface.addEventListener('touchcancel'", self.html)
        self.assertIn('Date.now() - lastHandledTouchTime < 500', self.html)

if __name__ == '__main__':
    unittest.main()
