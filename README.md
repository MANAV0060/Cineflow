# CineFlow Streaming Platform & REA

A modern, high-performance web streaming application with custom video player features (smooth seeking, audio dub switcher, resolution switcher, and live search recommendations), powered by reverse-engineered Moviebox streaming APIs.

---

## 📁 Project Structure

```
d:/REA/
├── app.py                             # Core Flask backend server & streaming remuxer
├── static/
│   └── index.html                     # CineFlow Single Page Application (UI + Custom Video Player)
├── requirements.txt                   # Python dependencies (Flask, requests)
├── API_WEBSITE_INTEGRATION_GUIDE.md   # API documentation & architecture guide
│
├── tests/                             # API and streaming test suites
│   ├── test_apis.py
│   ├── test_client_token.py
│   ├── test_gateway_config.py
│   ├── test_resolutions.py
│   ├── test_search_features.py
│   ├── test_tv_api.py
│   ├── test_visitor_login.py
│   ├── verify_apis.py
│   └── verify_playable_stream.py
│
├── reverse_engineering/               # APK analysis & reverse engineering assets
│   ├── apks/                          # Android application packages
│   │   ├── base.apk
│   │   └── origin.apk
│   ├── decompiled/                    # Jadx-decompiled source trees
│   ├── decompiled_origin/             # Decompiled origin package
│   ├── manifest_only/                 # Android manifest dumps
│   └── tools/                         # Static analysis & scanning tools
│       ├── fast_scan.py
│       ├── found_endpoints.txt
│       ├── moviebox_tool.py
│       ├── probe_domains.py
│       └── scan_apis.py
│
├── designs/                           # UI / UX reference designs
│   └── stitch_screens/                # Exported Google Stitch screen mockups
│
└── rea/                               # Reverse Engineering Assistant (REA) workspace
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/) installed and available in `PATH`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python app.py
```
Open your browser at **[http://localhost:5000](http://localhost:5000)**.

---

## ✨ Features

- **Movies & TV Series Catalog**: Trending, Popular, Top Rated, and Anime sections with responsive horizontal carousels.
- **Smart Predictive Search**: Fuzzy keyword search and categorized recommendations.
- **Enhanced Video Player**:
  - **Instant Buffer Seeking**: 0ms local in-memory seeking for fast skipping (+10s/-10s).
  - **Multi-Resolution Selector**: Switch dynamically between 1080p, 720p, and 480p.
  - **Audio Dubbing Selector**: Switch between Hindi Dubbed and Original tracks.
  - **Custom Controls**: Scrubbing timeline with loaded buffer progress, volume control, full-screen mode, and keyboard shortcuts (Space to Play/Pause, Left/Right arrows to skip).
