import sys
import unittest
import json
import urllib.request
import app
import anime_engine

class TestAnimeDubsAndSubtitles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.app.test_client()

    def test_01_aot_english_and_hindi_dubs(self):
        """Test Case 1: Attack on Titan has verified Japanese Original, English Dub, and Hindi Dub."""
        res = self.client.get('/api/dubs/anime_16498')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        dubs = data.get('dubs', [])
        self.assertGreaterEqual(len(dubs), 3)

        lan_codes = [d.get('lanCode') for d in dubs]
        self.assertIn('ja', lan_codes, "Original Japanese track must be available")
        self.assertIn('en', lan_codes, "English dub must be available")
        self.assertIn('hi', lan_codes, "Hindi dub must be available")

        # Verify exact English dub subjectId
        en_dub = next(d for d in dubs if d.get('lanCode') == 'en')
        self.assertEqual(en_dub.get('subjectId'), '8411756968024720848')
        self.assertIn('English', en_dub.get('lanName'))

        # Verify exact Hindi dub subjectId
        hi_dub = next(d for d in dubs if d.get('lanCode') == 'hi')
        self.assertEqual(hi_dub.get('subjectId'), '56988683026712168')
        self.assertIn('Hindi', hi_dub.get('lanName'))

        # Verify that English dub play-info returns actual playable DASH stream
        play_res = self.client.get('/api/play-info/8411756968024720848?se=1&ep=1')
        self.assertEqual(play_res.status_code, 200)
        play_data = play_res.get_json()
        self.assertIn('sacdn.hakunaymatata.com', play_data.get('url', ''))
        self.assertIn('8411756968024720848', play_data.get('url', ''))

    def test_02_demon_slayer_dubs_and_subtitles(self):
        """Test Case 2: Demon Slayer has English/Hindi dubs and multiple subtitles."""
        res = self.client.get('/api/dubs/anime_101922')
        self.assertEqual(res.status_code, 200)
        dubs = res.get_json().get('dubs', [])
        lan_codes = [d.get('lanCode') for d in dubs]
        self.assertIn('en', lan_codes)
        self.assertIn('hi', lan_codes)

        # Verify subtitles
        sub_res = self.client.get('/api/subtitles/anime_101922?se=1&ep=1')
        self.assertEqual(sub_res.status_code, 200)
        captions = sub_res.get_json().get('captions', [])
        self.assertGreater(len(captions), 0, "Demon Slayer must have subtitle captions")

        # Verify WebVTT subtitle conversion
        vtt_res = self.client.get('/api/vtt/anime_101922/en.vtt?se=1&ep=1')
        self.assertEqual(vtt_res.status_code, 200)
        self.assertTrue(vtt_res.data.startswith(b'WEBVTT'), "Subtitle must be valid WebVTT")

    def test_03_jujutsu_kaisen_dubs(self):
        """Test Case 3: Jujutsu Kaisen has Japanese Original, English Dub, and Hindi Dub."""
        res = self.client.get('/api/dubs/anime_113415')
        self.assertEqual(res.status_code, 200)
        dubs = res.get_json().get('dubs', [])
        lan_codes = [d.get('lanCode') for d in dubs]
        self.assertIn('ja', lan_codes)
        self.assertIn('en', lan_codes)
        self.assertIn('hi', lan_codes)

    def test_04_dragon_ball_dubs(self):
        """Test Case 4: Dragon Ball has verified Japanese Original, English Dub, and Hindi Dub."""
        res = self.client.get('/api/dubs/dragonball')
        self.assertEqual(res.status_code, 200)
        dubs = res.get_json().get('dubs', [])
        lan_codes = [d.get('lanCode') for d in dubs]
        self.assertIn('ja', lan_codes)
        self.assertIn('en', lan_codes)
        self.assertIn('hi', lan_codes)

    def test_05_aot_subtitles_and_vtt_format(self):
        """Test Case 5: Attack on Titan subtitle discovery and WebVTT conversion."""
        res = self.client.get('/api/subtitles/anime_16498?se=1&ep=1')
        self.assertEqual(res.status_code, 200)
        captions = res.get_json().get('captions', [])
        self.assertGreaterEqual(len(captions), 5)
        
        # Test WebVTT endpoint
        vtt_res = self.client.get('/api/vtt/anime_16498/en.vtt?se=1&ep=1')
        self.assertEqual(vtt_res.status_code, 200)
        self.assertTrue(vtt_res.data.startswith(b'WEBVTT'))
        self.assertIn(b'-->', vtt_res.data)

    def test_06_anime_engine_resolve_dub_vs_sub(self):
        """Test Case 6: anime_engine resolves distinct streams for dub vs sub."""
        dub_st = anime_engine.resolve_anime_stream(16498, ep=1, is_dub=True)
        sub_st = anime_engine.resolve_anime_stream(16498, ep=1, is_dub=False)
        self.assertIsNotNone(dub_st)
        self.assertIsNotNone(sub_st)
        self.assertNotEqual(dub_st['url'], sub_st['url'], "Dub stream URL must differ from original sub stream URL")
        self.assertIn('8411756968024720848', dub_st['url'], "Dub stream must use English dub SID")
        self.assertIn('1975770531236301600', sub_st['url'], "Sub stream must use Japanese SID")

if __name__ == '__main__':
    unittest.main()
