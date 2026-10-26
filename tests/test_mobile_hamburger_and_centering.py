import unittest
import re

class TestMobileHamburgerAndPlayerCentering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('index.html', 'r', encoding='utf-8') as f:
            cls.html = f.read()
        with open('static/index.html', 'r', encoding='utf-8') as f:
            cls.static_html = f.read()

    def test_01_index_and_static_identical(self):
        """Verify index.html and static/index.html are byte-for-byte in sync."""
        self.assertEqual(self.html, self.static_html, "index.html and static/index.html must be identical")

    def test_02_hamburger_navigation_sections(self):
        """Verify hamburger navigation drawer contains Anime, Live TV, Movies, and Series."""
        # 1. Drawer element with high z-index
        self.assertIn('id="mobile-nav-drawer"', self.html)
        self.assertIn('z-[80]', self.html)

        # 2. Anime section
        self.assertIn("mobileNavSelect('anime')", self.html)
        # 3. Live TV section
        self.assertIn("mobileNavSelect('livetv')", self.html)
        self.assertIn('Live TV', self.html)
        # 4. Movies section
        self.assertIn("mobileNavSelect('movie')", self.html)
        # 5. Series section
        self.assertIn("mobileNavSelect('tv')", self.html)

    def test_03_center_controls_absolute_centering(self):
        """Verify center HUD controls are pinned with true viewport centering top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2."""
        match = re.search(r'id="center-hud-controls"[^>]+class="([^"]+)"', self.html)
        self.assertIsNotNone(match, "#center-hud-controls element must exist")
        classes = match.group(1)
        self.assertIn('top-1/2', classes)
        self.assertIn('left-1/2', classes)
        self.assertIn('-translate-x-1/2', classes)
        self.assertIn('-translate-y-1/2', classes)
        self.assertNotIn('my-auto', classes, "my-auto must not be used on center controls")

    def test_04_buffering_spinner_no_whole_screen_blur(self):
        """Verify buffering spinner does not cover screen in blurry backdrop fog."""
        match = re.search(r'id="player-loading-spinner"[^>]+class="([^"]+)"', self.html)
        self.assertIsNotNone(match, "#player-loading-spinner must exist")
        classes = match.group(1)
        self.assertNotIn('backdrop-blur-sm bg-black/50', classes, "No whole-screen blur overlay")
        self.assertIn('pointer-events-none', classes)

    def test_05_hud_pointer_events_delegation(self):
        """Verify #player-hud remains pointer-events-none and delegates pointer-events-auto only to .hud-interactive."""
        match = re.search(r'id="player-hud"[^>]+class="([^"]+)"', self.html)
        self.assertIsNotNone(match, "#player-hud must exist")
        classes = match.group(1)
        self.assertIn('pointer-events-none', classes)
        self.assertIn('.hud-interactive', self.html)
        self.assertIn("hud.style.pointerEvents = 'none'", self.html)

    def test_06_auto_hide_timeout_3_seconds(self):
        """Verify auto-hide timeout is approximately 3 seconds during active playback."""
        self.assertIn('3000', self.html)

    def test_07_seek_feedback_circular_glassmorphism(self):
        """Verify seek feedback badges have circular dark-glass styling matching play/pause button."""
        left_match = re.search(r'id="double-tap-left"[^>]*>([\s\S]*?)</div>\s*</div>', self.html)
        self.assertIsNotNone(left_match)
        content = left_match.group(1)
        self.assertIn('rounded-full', content)
        self.assertIn('bg-black/60', content)
        self.assertIn('backdrop-blur-md', content)
        self.assertIn('border-white/20', content)

if __name__ == '__main__':
    unittest.main()
