# BookSeeker

A self-hosted web app for searching, downloading, and managing audiobooks and ebooks. Search torrent trackers via [Prowlarr](https://github.com/Prowlarr/Prowlarr), download with [qBittorrent](https://github.com/qbittorrent/qBittorrent), and manage your library through [Audiobookshelf](https://github.com/advplyr/audiobookshelf) and [Calibre-Web](https://github.com/janeczku/calibre-web).

## Screenshots

### Login
![Login](screenshots/01-login.png)

### Audiobook Search
Search across multiple torrent trackers with one click. Toggle between audiobook and ebook search modes.

![Audiobook Search](screenshots/02-search.png)

### Ebook Search
Switch to ebook mode to find epubs, PDFs, and other ebook formats.

![Ebook Search](screenshots/07-ebook-search.png)

### Library
Browse your Audiobookshelf library with cover art, duration, and metadata.

![Library](screenshots/03-library.png)

### Ebook File Browser
Browse and download ebook files directly to your device.

![Ebooks](screenshots/05-ebooks.png)

### Downloads
Monitor active torrent downloads with real-time progress tracking.

![Downloads](screenshots/04-downloads.png)

### Player (Audiobookshelf)
Embedded Audiobookshelf player — listen to audiobooks without leaving the app.

![Player](screenshots/08-player.png)

### Reader (Calibre-Web)
Embedded Calibre-Web reader — browse and read ebooks without leaving the app.

![Reader](screenshots/09-reader.png)

### Settings
Admin panel with password management, service configuration, user management, and disk usage monitoring.

![Settings](screenshots/06-settings.png)

## Features

- **Audiobook & Ebook Search** — Search multiple torrent trackers via Prowlarr (audio category 3000, books category 7000)
- **One-Click Downloads** — Send torrents to qBittorrent with automatic save path routing
- **Audiobookshelf Integration** — Browse your audiobook library with covers, metadata, and automatic library scanning after downloads
- **Ebook File Browser** — Browse downloaded ebooks and download them directly to your phone/device
- **Calibre-Web Integration** — Embedded Calibre-Web reader accessible from the app
- **Embedded Players** — Access Audiobookshelf player and Calibre-Web reader without leaving the app (reverse-proxied through the backend)
- **User Management** — Admin can create/delete users, each user can change their own password
- **Settings Panel** — Configure all service URLs and API keys from the UI
- **Disk Usage** — Monitor and manage storage, delete audiobook folders with automatic ABS library scan
- **Dark UI** — Clean, responsive dark theme

## Architecture

```
BookSeeker (FastAPI + vanilla JS SPA)
├── Prowlarr        — torrent indexer aggregator
├── qBittorrent     — torrent client (behind Gluetun VPN)
├── Audiobookshelf  — audiobook library manager & player
└── Calibre-Web     — ebook library manager & reader
```

## Quick Start

### Docker Compose

```bash
git clone https://github.com/lucashanak/BookSeeker.git
cd BookSeeker
cp .env.example .env  # edit with your values
docker compose up -d
```

### Standalone Docker

```bash
docker build -t book-seeker .

docker run -d --name book-seeker \
  -p 8091:8091 \
  -v ./data:/app/data \
  -v /path/to/audiobooks:/audiobooks \
  -v /path/to/ebooks:/ebooks \
  -e PROWLARR_URL=http://prowlarr:9696 \
  -e PROWLARR_API_KEY=your-api-key \
  -e QBIT_URL=http://qbittorrent:8081 \
  -e ABS_URL=http://audiobookshelf:80 \
  -e ABS_USER=admin \
  -e ABS_PASS=your-abs-password \
  -e ADMIN_USER=admin \
  -e ADMIN_PASS=your-admin-password \
  -e QBIT_SAVE_PATH=/data/audiobooks \
  -e QBIT_EBOOK_SAVE_PATH=/data/ebooks \
  -e EBOOK_DIR=/ebooks \
  -e CALIBRE_URL=http://calibre-web:8083 \
  book-seeker
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `PROWLARR_URL` | Prowlarr API URL | `http://prowlarr:9696` |
| `PROWLARR_API_KEY` | Prowlarr API key | — |
| `QBIT_URL` | qBittorrent Web UI URL | `http://localhost:8081` |
| `ABS_URL` | Audiobookshelf URL | `http://audiobookshelf:80` |
| `ABS_USER` | Audiobookshelf username | `admin` |
| `ABS_PASS` | Audiobookshelf password | — |
| `ADMIN_USER` | BookSeeker admin username | `admin` |
| `ADMIN_PASS` | BookSeeker admin password | — |
| `QBIT_SAVE_PATH` | qBittorrent save path for audiobooks | — |
| `QBIT_EBOOK_SAVE_PATH` | qBittorrent save path for ebooks | — |
| `EBOOK_DIR` | Ebook directory mount path | `/ebooks` |
| `CALIBRE_URL` | Calibre-Web URL | `http://calibre-web:8083` |
| `PORT` | Server port | `8091` |

## Tech Stack

- **Backend:** Python 3.11, FastAPI, httpx
- **Frontend:** Vanilla JavaScript SPA, CSS
- **Container:** Docker
- **Services:** Prowlarr, qBittorrent, Audiobookshelf, Calibre-Web

## License

MIT
