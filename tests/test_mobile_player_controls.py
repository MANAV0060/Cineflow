import os
import sys
import unittest
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class TestMobilePlayerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('index.html', 'r', encoding='utf-8') as f:
            cls.html = f.read()
        with open('static/index.html', 'r', encoding='utf-8') as f:
            cls.static_html = f.read()

    def test_01_index_and_static_synchronized(self):
        """Verify that index.html and static/index.html are completely in sync."""
        self.assertEqual(len(self.html), len(self.static_html), "index.html and static/index.html length must match")
        self.assertEqual(self.html, self.static_html, "index.html and static/index.html contents must be identical")

    def test_02_mobile_livetv_button_presence(self):
        """Verify that mobile navigation header includes a prominent Live TV button."""
        # 1. Header mobile button
        self.assertIn('id="btn-mobile-livetv"', self.html)
        self.assertIn('showLiveTvSection()', self.html)
        self.assertIn('live_tv', self.html)
        self.assertIn('animate-pulse', self.html)

        # 2. Settings modal shortcut
        self.assertIn('Switch to Live TV', self.html)
        self.assertIn('toggleSettingsModal(); exitPlayer(); showLiveTvSection();', self.html)

    def test_03_fullscreen_episode_drawer_dom_architecture(self):
        """Verify episode drawer backdrop and dynamic fullscreen parenting."""
        # 1. Backdrop overlay
        self.assertIn('id="modal-episodes-backdrop"', self.html)
        self.assertIn('onclick="toggleEpisodesDrawer()"', self.html)
        self.assertIn('z-[65]', self.html)

        # 2. Drawer container
        self.assertIn('id="modal-episodes-drawer"', self.html)
        self.assertIn('z-[70]', self.html)
        self.assertIn('max-h-[100dvh]', self.html)
        self.assertIn('overflow-hidden', self.html)

        # 3. Dynamic parenting function
        self.assertIn('function ensureEpisodesDrawerParent()', self.html)
        self.assertIn('targetParent.appendChild(drawer)', self.html)
        self.assertIn('targetParent.appendChild(backdrop)', self.html)

        # 4. Trigger calls
        self.assertIn('ensureEpisodesDrawerParent();', self.html)
        self.assertIn('function closeEpisodesDrawer()', self.html)

    def test_04_double_tap_gestures_and_ui_ripple(self):
        """Verify double tap indicators, labels, and touch gesture engine."""
        # 1. Indicators with labels and chevrons
        self.assertIn('id="double-tap-left"', self.html)
        self.assertIn('id="double-tap-left-label"', self.html)
        self.assertIn('-10 seconds', self.html)
        self.assertIn('fast_rewind', self.html)

        self.assertIn('id="double-tap-right"', self.html)
        self.assertIn('id="double-tap-right-label"', self.html)
        self.assertIn('+10 seconds', self.html)
        self.assertIn('fast_forward', self.html)

        # 2. Touch event listeners in setupVideoGestures
        self.assertIn("surface.addEventListener('touchstart'", self.html)
        self.assertIn("surface.addEventListener('touchmove'", self.html)
        self.assertIn("surface.addEventListener('touchend'", self.html)
        self.assertIn("surface.addEventListener('touchcancel'", self.html)

        # 3. Movement threshold rejection to prevent conflict with scrolling/swiping
        self.assertIn('dx > 12 || dy > 12', self.html)
        self.assertIn('touchMoved = true', self.html)

        # 4. Repeated double-tap accumulation
        self.assertIn('accumulatedSeconds += 10', self.html)
        self.assertIn('showDoubleTapFeedback(side, accumulatedSeconds)', self.html)

        # 5. Live stream protection (no seeking on Live TV)
        self.assertIn('const isLive = !!currentLiveChannel;', self.html)

    def test_05_pointer_events_and_center_hud_clearing(self):
        """Verify that center HUD outer wrapper does not intercept touches intended for click surface."""
        # Check that outer #center-hud-controls has pointer-events-none
        match = re.search(r'id="center-hud-controls"[^>]+class="([^"]+)"', self.html)
        self.assertIsNotNone(match)
        classes = match.group(1)
        self.assertIn('pointer-events-none', classes, "Outer center HUD wrapper must be pointer-events-none")

        # Check inner cluster has pointer-events-auto
        self.assertIn('pointer-events-auto', self.html)

    def test_06_touch_targets_and_safe_areas(self):
        """Verify mobile safe area insets and comfortable touch targets."""
        self.assertIn('safe-area-inset-top', self.html)
        self.assertIn('safe-area-inset-bottom', self.html)
        self.assertIn('safe-area-inset-left', self.html)
        self.assertIn('safe-area-inset-right', self.html)

        # Episodes button has hidden flex for proper display when unhidden
        self.assertIn('id="btn-episodes-drawer"', self.html)
        self.assertIn('hidden flex w-9 h-9 sm:w-10 sm:h-10', self.html)

if __name__ == '__main__':
    unittest.main()
