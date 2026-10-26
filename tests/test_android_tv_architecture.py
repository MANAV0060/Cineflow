import os
import sys
import unittest
import xml.etree.ElementTree as ET
import subprocess
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class TestAndroidTvArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.tv_dir = os.path.join(cls.root_dir, "android-tv")
        cls.manifest_path = os.path.join(cls.tv_dir, "app", "src", "main", "AndroidManifest.xml")
        cls.app_gradle_path = os.path.join(cls.tv_dir, "app", "build.gradle.kts")
        cls.keystore_path = os.path.join(cls.tv_dir, "keystore", "cineflow-release-key.jks")

    def test_01_android_manifest_tv_profile(self):
        """Verify AndroidManifest has full Leanback TV profile, permissions and launcher."""
        self.assertTrue(os.path.exists(self.manifest_path), "AndroidManifest.xml must exist")
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Leanback TV hardware flags
        self.assertIn('android:name="android.software.leanback"', content)
        self.assertIn('android:required="true"', content)
        self.assertIn('android:name="android.hardware.touchscreen"', content)
        self.assertIn('android:required="false"', content)

        # Essential TV permissions
        self.assertIn('android.permission.INTERNET', content)
        self.assertIn('android.permission.REQUEST_INSTALL_PACKAGES', content)
        self.assertIn('android.permission.WAKE_LOCK', content)

        # TV Launcher intent
        self.assertIn('android.intent.category.LEANBACK_LAUNCHER', content)
        self.assertIn('android:banner="@drawable/tv_banner"', content)

        # FileProvider for seamless in-app APK upgrades
        self.assertIn('androidx.core.content.FileProvider', content)
        self.assertIn('${applicationId}.fileprovider', content)

    def test_02_gradle_build_and_signing_configuration(self):
        """Verify build.gradle.kts has com.cineflow.tv, release signing, and ExoPlayer."""
        self.assertTrue(os.path.exists(self.app_gradle_path), "app/build.gradle.kts must exist")
        with open(self.app_gradle_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('applicationId = "com.cineflow.tv"', content)
        self.assertIn('versionCode = 1001', content)
        self.assertIn('storeFile = file("../keystore/cineflow-release-key.jks")', content)
        self.assertIn('keyAlias = "cineflow"', content)
        self.assertIn('enableV1Signing = true', content)
        self.assertIn('enableV2Signing = true', content)

        # Media3 / ExoPlayer dependencies
        self.assertIn('androidx.media3:media3-exoplayer', content)
        self.assertIn('androidx.leanback:leanback', content)

    def test_03_release_keystore_validity(self):
        """Verify that the permanent release keystore exists and is valid."""
        self.assertTrue(os.path.exists(self.keystore_path), "cineflow-release-key.jks must exist")
        self.assertGreater(os.path.getsize(self.keystore_path), 1000, "Keystore file must not be empty")

    def test_04_remote_dpad_focus_and_animations(self):
        """Verify TV focus feedback animations and presenters."""
        animator_path = os.path.join(self.tv_dir, "app", "src", "main", "res", "animator", "card_focus_animator.xml")
        self.assertTrue(os.path.exists(animator_path), "card_focus_animator.xml must exist")
        with open(animator_path, 'r', encoding='utf-8') as f:
            anim = f.read()
        self.assertIn('scaleX', anim)
        self.assertIn('scaleY', anim)
        self.assertIn('1.08', anim)

        card_presenter = os.path.join(self.tv_dir, "app", "src", "main", "java", "com", "cineflow", "tv", "ui", "main", "CardPresenter.kt")
        with open(card_presenter, 'r', encoding='utf-8') as f:
            cp = f.read()
        self.assertIn('card_focus_animator', cp)
        self.assertIn('isFocusable = true', cp)

    def test_05_player_cumulative_seeking(self):
        """Verify PlaybackActivity implements remote D-pad seeking accumulation."""
        player_path = os.path.join(self.tv_dir, "app", "src", "main", "java", "com", "cineflow", "tv", "ui", "player", "PlaybackActivity.kt")
        with open(player_path, 'r', encoding='utf-8') as f:
            code = f.read()
        self.assertIn('KeyEvent.KEYCODE_DPAD_RIGHT', code)
        self.assertIn('KeyEvent.KEYCODE_DPAD_LEFT', code)
        self.assertIn('handleCumulativeSeek', code)
        self.assertIn('accumulatedSeekSeconds', code)
        self.assertIn('seekFeedbackText', code)

    def test_06_in_app_updater_and_backend_endpoints(self):
        """Verify AppUpdater implementation and backend /api/tv/update endpoint."""
        updater_path = os.path.join(self.tv_dir, "app", "src", "main", "java", "com", "cineflow", "tv", "util", "AppUpdater.kt")
        with open(updater_path, 'r', encoding='utf-8') as f:
            code = f.read()
        self.assertIn('checkForUpdates', code)
        self.assertIn('downloadAndInstallApk', code)
        self.assertIn('FileProvider.getUriForFile', code)
        self.assertIn('application/vnd.android.package-archive', code)

        # Check app.py has /api/tv/update and /api/tv/download
        app_path = os.path.join(self.root_dir, "app.py")
        with open(app_path, 'r', encoding='utf-8') as f:
            app_code = f.read()
        self.assertIn('/api/tv/update', app_code)
        self.assertIn('/api/tv/download', app_code)

if __name__ == '__main__':
    unittest.main()
