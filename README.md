# StepDaddyLiveHD

A self-hosted IPTV proxy built with [Reflex](https://reflex.dev), enabling you to watch over 1,000 TV channels and search for live events or sports channels. Stream directly in your browser or through any media player client. You can also download the entire playlist (`playlist.m3u8`) and integrate it with platforms like Jellyfin or IPTV media players.

## Features

- **Stream Anywhere**: Watch TV channels on any device via the web or media player clients.
- **Event Search**: Quickly find the right channel for live events or sports.
- **Playlist Integration**: Download the `playlist.m3u8` file and use it with Jellyfin or other IPTV clients.
- **Customizable Hosting**: Host the application on your PC or deploy it via Docker with various configuration options.

---

## Installation

### Local Installation

1. Install Python (tested with version 3.12).
2. Clone the repository and navigate to the project directory.
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Initialize Reflex:
   ```bash
   reflex init
   ```
6. Run the application in production mode:
   ```bash
   reflex run --env prod
   ```

### Docker Installation

1. Docker Installation:
   ```bash
   docker build -t step-daddy-live-hd .
   ```
2. Run the container:
   ```bash
   docker run -p 3000:3000 step-daddy-live-hd
   ```

---

## Configuration

### Environment Variables
- **PORT**: Specify a custom port for the application.
- **API_URL**: Set the domain for hosting behind a custom domain.
- **SOCKS5**: Proxy requests to DLHD through your server.
- **PROXY_CONTENT**: Proxy the content/streams through your server.

### Example Docker Command
   ```bash
   docker build --build-arg PROXY_CONTENT=FALSE --build-arg API_URL=https://example.com --build-arg SOCKS5=user:password@proxy.example.com:1080 -t step-daddy-live-hd .
   docker run -e PROXY_CONTENT=FALSE -e API_URL=https://example.com -e SOCKS5=user:password@proxy.example.com:1080 -p 3000:3000 step-daddy-live-hd
   ```

---

## Site Map

### Pages

1. **Home**: Browse and search for TV channels.
2. **Live Events**: Find channels streaming live sports or events.
3. **Playlist Download**: Download the playlist.m3u8 file for integration with media players.

---

## Screenshots
Home Page
<img alt="Home Page" src="https://files.catbox.moe/qlqqs5.png">
Watch Page
<img alt="Watch Page" src="https://files.catbox.moe/974r9w.png">
Live Events
<img alt="Live Events" src="https://files.catbox.moe/7oawie.png">

---

## Hosting Options
Refer to the [Reflex documentation](https://reflex.dev/docs/hosting/self-hosting/) for additional self-hosting methods.