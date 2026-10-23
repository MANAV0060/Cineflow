<div align="center">

# 🎬 Cineflow
### Next-Generation Cinematic Web Streaming Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Cineflow** is an ultra-fast, modern web streaming platform that delivers a theatre-grade entertainment experience for movies, television series, and anime. Built with a custom zero-flicker video player engine, an interactive semicircular episode dial, real-time predictive search, multi-language audio dubbing, and responsive design across all devices.

[Live Demo](https://cineflow-mocha.vercel.app/) • [Features](#-features--whats-in-the-project) • [Key Benefits](#-why-cineflow-key-benefits) • [Quick Start](#-quick-start) • [Shortcuts](#️-keyboard-shortcuts--gestures)

</div>

---

## 🌟 Why Cineflow? (Key Benefits)

- **⚡ Zero-Flicker Playback & Instant Seeking**: An intelligent canvas frame-freeze engine holds the last visible frame during seeks and buffer phases, eliminating jarring black screens.
- **📱 True Multi-Device Responsiveness**: Tailored viewports for smartphones, tablets, laptops, and ultra-wide desktop monitors without broken grids, squashed text, or horizontal page wobble.
- **🎧 Multi-Language Audio Dub Switcher**: Seamlessly switch between original audio tracks and international/regional dubs (such as Hindi Dubbed, Spanish, and Portuguese) directly from the player HUD.
- **💬 Smart Subtitle Alignment Engine**: Cinema-grade subtitle rendering with customizable font sizes, dynamic vertical offsets, and automatic elevation above player controls to prevent overlapping.
- **🎡 Interactive Semicircular Episode Dial**: A distinctive, curved arc episode selector with smooth mouse-wheel rotation, touch swipe navigation, and responsive scaling.
- **🔍 Real-Time Predictive Search**: Instant debounce search suggestions with categorized recommendations and one-click filtering.
- **🚀 Lightweight & Dependency-Free Frontend**: Built as a pure Single-Page Application (SPA) without bloated client frameworks, achieving sub-second load times and silky-smooth 60fps animations.
- **☁️ Cloud-Ready Deployment**: Pre-configured for serverless edge deployment on **Vercel** and high-concurrency backend hosting on **Render** / **Docker**.

---

## ✨ Features & What's In The Project

### 1. 🏠 Homepage & Catalog Discovery
- **Atmospheric Hero Showcase**: Dynamic feature banner showcasing top-rated titles with fluid typography, backdrop atmosphere, rating metrics, and a swipeable stills strip.
- **Adaptive 4-Tier Content Grids**: Fluid 2 to 6 column card grid (`grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6`) ensuring ideal card proportions on mobile, tablet, and desktop screens.
- **Category Filter Carousel**: Smooth horizontal-scrolling category pills (Trending, Movies, TV Series, Anime) with active state indicators.
- **Spotlight Banners**: Highlighted cinematic feature showcases with CRT scanline textures and neon glow accents.
- **Mobile Navigation Drawer**: Responsive slide-down navigation drawer accessible via hamburger menu on mobile and tablet screens.

### 2. 🎞️ Movie & TV Series Detail View
- **Atmospheric Visual Stage**: High-contrast backdrop visuals with CRT scanline textures and moody ambient lighting.
- **Comprehensive Metadata Deck**: Release year, runtime, age ratings (18+, PG-13), genre tags, IMDb rating scores, and 4K UHD / Atmos badges.
- **Audio Dub Discovery Row**: Real-time badges displaying all available dubbed audio tracks before playback starts.
- **Responsive Episode Dial**: Grand semicircular arc selector for TV shows that dynamically scales to viewport width.
- **Episodes & Seasons Drawer**: Quick-access global slide-over drawer to browse large catalogs across all seasons and episodes.

### 3. 🎥 Cinema Video Player
- **High-Speed HTML5 Stream Engine**: Hardware-accelerated streaming with chunked byte-range requests for smooth playback.
- **Precision Scrubber Timeline**: Dual-layer track showing loaded buffer progress, played progress bar, and hover/touch timestamp tooltip.
- **Dynamic Quality Switcher**: Adaptive resolution selector supporting 1080p FHD, 720p HD, and 480p SD streams.
- **Audio & Subtitle Customizer**: Modal drawer to toggle tracks, adjust subtitle font size (16px – 34px), and customize vertical elevation.
- **Mobile Touch Gestures**: Double-tap left/right ripples to skip ±10 seconds, and automatic landscape mode when entering fullscreen.
- **Playback Controls**: Ambient center play/pause indicator, playback speed multiplier (0.5x – 2.0x), Picture-in-Picture (PiP), and volume slider.

### 4. ⚡ Backend Streaming Gateway
- **Python Flask Architecture**: Lightweight API server handling catalog aggregation, search queries, and stream resolution mapping.
- **Stream Remuxer & Proxy**: High-performance HTTP streaming proxy with range-header support for seamless media scrubbing.
- **Gunicorn Concurrency**: Production-ready multi-threaded worker configuration for concurrent streaming requests.

---

## 📁 Project Structure

```
Cineflow/
├── app.py                             # Core Flask backend server & streaming gateway
├── index.html                         # Cineflow Single Page Application (UI + Custom Player)
├── static/
│   └── index.html                     # Production-synced static frontend build
├── vercel.json                        # Vercel deployment & API rewrite configuration
├── Dockerfile                         # Container build definition for backend deployment
├── requirements.txt                   # Python dependencies (Flask, requests, gunicorn)
├── API_WEBSITE_INTEGRATION_GUIDE.md   # Comprehensive API documentation & data schemas
├── DEPLOYMENT_VERCEL_RENDER_AUTOBOT.md# Cloud deployment architecture and guides
└── tests/                             # Automated test suites for endpoints & streaming
    ├── test_apis.py                   # API response and schema validation
    ├── test_tv_api.py                 # TV series and episode structure tests
    ├── test_search_features.py        # Autocomplete and search query tests
    └── verify_playable_stream.py      # Stream remuxing and playback verification
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **FFmpeg** (Optional, recommended for local media remuxing)

### 1. Clone the Repository
```bash
git clone https://github.com/MANAV0060/Cineflow.git
cd Cineflow
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
python app.py
```

The application will start at **[http://localhost:5000](http://localhost:5000)**.

---

## ☁️ Deployment

### Deploying Frontend to Vercel
The frontend is ready for zero-configuration deployment on **Vercel**:
1. Push the repository to GitHub.
2. Import the repository in your Vercel Dashboard.
3. Vercel automatically detects `vercel.json` and routes `/api/*` to the streaming backend.

### Deploying Backend to Render or Docker
Deploy using the included `Dockerfile` or Render Web Service:
```bash
# Build the Docker image
docker build -t cineflow-api .

# Run the container
docker run -p 5000:5000 -e PORT=5000 cineflow-api
```

---

## ⌨️ Keyboard Shortcuts & Gestures

| Key / Gesture | Action |
| :--- | :--- |
| <kbd>Space</kbd> / <kbd>K</kbd> | Play / Pause playback |
| <kbd>→</kbd> / <kbd>L</kbd> | Skip forward 10 seconds |
| <kbd>←</kbd> / <kbd>J</kbd> | Skip backward 10 seconds |
| <kbd>F</kbd> | Toggle Fullscreen mode |
| <kbd>M</kbd> | Mute / Unmute audio |
| <kbd>C</kbd> | Open Audio & Subtitles customization modal |
| <kbd>S</kbd> | Open Video Player Settings modal |
| <kbd>Esc</kbd> | Close any open modal or drawer |
| **Double Tap (Left / Right)** | Skip ±10 seconds on mobile / tablet touchscreens |
| **Mouse Wheel / Trackpad** | Rotate episode cards on the semicircular carousel |

---

## 🛡️ License & Disclaimer

This project is licensed under the **MIT License**.

> **Disclaimer:** Cineflow is an open-source educational project developed for demonstrating modern frontend architecture, custom HTML5 video player engineering, and responsive UI design. All media metadata, posters, and thumbnails belong to their respective copyright holders.
