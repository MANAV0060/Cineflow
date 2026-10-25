import unittest
import json
import urllib.parse
import app
import anime_engine

class TestAnimeSubtitlesRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.app.test_client()

    def test_01_aot_subtitles_discovery(self):
        """Test 1: Attack on Titan subtitle discovery returns valid caption tracks including English."""
        res = self.client.get('/api/subtitles/anime_16498?se=1&ep=1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        captions = data.get('captions', [])
        self.assertGreaterEqual(len(captions), 5, "AoT must have multiple subtitle tracks")

        langs = [(c.get('language') or c.get('languageCode') or '').lower() for c in captions]
        self.assertIn('en', langs, "English subtitle must be available for AoT")

        # Verify caption structure
        en_cap = next(c for c in captions if (c.get('language') or '').lower() == 'en')
        self.assertTrue(en_cap.get('url'), "Caption must have valid download URL")
        self.assertIn('https://', en_cap.get('url'))

    def test_02_demon_slayer_subtitles_discovery(self):
        """Test 2: Demon Slayer subtitle discovery returns valid tracks including English."""
        res = self.client.get('/api/subtitles/anime_101922?se=1&ep=1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        captions = data.get('captions', [])
        self.assertGreaterEqual(len(captions), 1, "Demon Slayer must have subtitle tracks")

        langs = [(c.get('language') or c.get('languageCode') or '').lower() for c in captions]
        self.assertIn('en', langs, "English subtitle must be available for Demon Slayer")

    def test_03_vtt_endpoint_conversion(self):
        """Test 3: /api/vtt conversion produces compliant WebVTT cues."""
        res = self.client.get('/api/vtt/anime_16498/en.vtt?se=1&ep=1')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/vtt')
        self.assertTrue(res.data.startswith(b'WEBVTT'), "Response must start with WEBVTT header")
        self.assertIn(b'-->', res.data, "Response must contain timestamp cue arrows")
        # Subtitle timestamps must use dot separators for milliseconds
        self.assertIn(b'.', res.data)

    def test_04_subtitle_file_direct_proxy(self):
        """Test 4: /api/subtitle-file endpoint proxies direct signed subtitle URLs."""
        sub_res = self.client.get('/api/subtitles/anime_16498?se=1&ep=1')
        captions = sub_res.get_json().get('captions', [])
        en_cap = next(c for c in captions if (c.get('language') or '').lower() == 'en')
        sub_url = en_cap.get('url')

        proxy_res = self.client.get(f'/api/subtitle-file?url={urllib.parse.quote(sub_url)}')
        self.assertEqual(proxy_res.status_code, 200)
        self.assertEqual(proxy_res.mimetype, 'text/vtt')
        self.assertTrue(proxy_res.data.startswith(b'WEBVTT'))
        self.assertIn(b'-->', proxy_res.data)

    def test_05_srt_to_vtt_format_conversion(self):
        """Test 5: srt_to_vtt handles comma timestamps, BOM, and line endings."""
        raw_srt = "\ufeff1\r\n00:00:20,123 --> 00:00:24,456\r\nHello, world!\r\n\r\n2\r\n00:00:25,000 --> 00:00:28,500\r\nSecond line."
        vtt = app.srt_to_vtt(raw_srt)
        self.assertTrue(vtt.startswith("WEBVTT\n"))
        self.assertIn("00:00:20.123 --> 00:00:24.456", vtt)
        self.assertIn("00:00:25.000 --> 00:00:28.500", vtt)
        self.assertNotIn("\ufeff", vtt)

    def test_06_frontend_subtitle_pipeline_presence(self):
        """Test 6: Verify frontend contains subtitle rendering, direct proxy, and synchronization logic."""
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        self.assertIn('function parseVTT', html)
        self.assertIn('function renderActiveSubtitle', html)
        self.assertIn('function loadVttTrack', html)
        self.assertIn('/api/subtitle-file', html)
        self.assertIn('player-subtitle-container', html)
        self.assertIn('player-subtitle-text', html)
        self.assertIn("video.addEventListener('seeked'", html)

if __name__ == '__main__':
    unittest.main()
