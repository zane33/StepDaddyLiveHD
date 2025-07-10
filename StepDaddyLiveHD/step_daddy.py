import json
import re
import reflex as rx
import logging
import asyncio
from urllib.parse import quote, urlparse
from curl_cffi import AsyncSession
from typing import List
from .utils import encrypt, decrypt, urlsafe_base64, extract_and_decode_var
from rxconfig import config

logger = logging.getLogger(__name__)


class Channel(rx.Base):
    id: str
    name: str
    tags: List[str]
    logo: str


class StepDaddy:
    def __init__(self):
        socks5 = config.socks5
        session_config = {
            "timeout": 30,  # Add timeout to prevent hanging requests
            "impersonate": "chrome110",  # Better browser impersonation
            "max_redirects": 5,  # Limit redirects
        }
        
        if socks5:
            session_config["proxy"] = f"socks5://{socks5}"
        
        self._session = AsyncSession(**session_config)
        self._base_url = config.daddylive_uri
        self.channels = []
        self._load_lock = asyncio.Lock()  # Prevent concurrent channel loading
        with open("StepDaddyLiveHD/meta.json", "r") as f:
            self._meta = json.load(f)

    def _headers(self, referer: str = None, origin: str = None):
        if referer is None:
            referer = self._base_url
        headers = {
            "Referer": referer,
            "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
        }
        if origin:
            headers["Origin"] = origin
        return headers

    async def load_channels(self):
        # Use lock to prevent concurrent loading
        async with self._load_lock:
            channels = []
            try:
                logger.info(f"Fetching channels from {self._base_url}/24-7-channels.php")
                response = await self._session.get(f"{self._base_url}/24-7-channels.php", headers=self._headers())

                if response.status_code != 200:
                    logger.error(f"Failed to fetch channels: HTTP {response.status_code}")
                    return

                channels_block = re.compile("<center><h1(.+?)tab-2", re.MULTILINE | re.DOTALL).findall(str(response.text))

                if not channels_block:
                    logger.error("No channels block found in response")
                    return

                channels_data = re.compile("href=\"(.*)\" target(.*)<strong>(.*)</strong>").findall(channels_block[0])

                # Process channels concurrently for better performance
                tasks = []
                for channel_data in channels_data:
                    tasks.append(self._process_channel_data(channel_data))
                
                # Wait for all channel processing to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error processing channel: {str(result)}")
                    elif result is not None:
                        channels.append(result)

                logger.info(f"Successfully processed {len(channels)} channels")
            except Exception as e:
                logger.error(f"Error loading channels: {str(e)}")
                # Don't raise the exception, just log it and keep existing channels
            finally:
                if channels:  # Only update if we successfully loaded channels
                    self.channels = sorted(channels, key=lambda channel: (channel.name.startswith("18"), channel.name))

    async def _process_channel_data(self, channel_data):
        """Process a single channel data asynchronously"""
        try:
            return self._get_channel(channel_data)
        except Exception as e:
            logger.error(f"Error processing channel {channel_data}: {str(e)}")
            return None

    def _get_channel(self, channel_data) -> Channel:
        channel_id = channel_data[0].split('-')[1].replace('.php', '')
        channel_name = channel_data[2]
        if channel_id == "666":
            channel_name = "Nick Music"
        if channel_id == "609":
            channel_name = "Yas TV UAE"
        if channel_data[2] == "#0 Spain":
            channel_name = "Movistar Plus+"
        elif channel_data[2] == "#Vamos Spain":
            channel_name = "Vamos Spain"
        clean_channel_name = re.sub(r"\s*\(.*?\)", "", channel_name)
        meta = self._meta.get(clean_channel_name, {})
        logo = meta.get("logo", "/missing.png")
        if logo.startswith("http"):
            logo = f"{config.api_url}/logo/{urlsafe_base64(logo)}"
        return Channel(id=channel_id, name=channel_name, tags=meta.get("tags", []), logo=logo)

    async def stream(self, channel_id: str):
        try:
            url = f"{self._base_url}/stream/stream-{channel_id}.php"
            if len(channel_id) > 3:
                url = f"{self._base_url}/stream/bet.php?id=bet{channel_id}"
            
            # Use semaphore to limit concurrent stream requests
            async with self._get_stream_semaphore():
                response = await self._session.post(url, headers=self._headers())
                source_url = re.compile("iframe src=\"(.*)\" width").findall(response.text)[0]
                source_response = await self._session.post(source_url, headers=self._headers(url))

                # Not generic
                channel_key = re.compile(r"var\s+channelKey\s*=\s*\"(.*?)\";").findall(source_response.text)[-1]
                auth_ts = extract_and_decode_var("__c", source_response.text)
                auth_sig = extract_and_decode_var("__e", source_response.text)
                auth_path = extract_and_decode_var("__b", source_response.text)
                auth_rnd = extract_and_decode_var("__d", source_response.text)
                auth_url = extract_and_decode_var("__a", source_response.text)
                auth_request_url = f"{auth_url}{auth_path}?channel_id={channel_key}&ts={auth_ts}&rnd={auth_rnd}&sig={auth_sig}"
                auth_response = await self._session.get(auth_request_url, headers=self._headers(source_url))
                if auth_response.status_code != 200:
                    raise ValueError("Failed to get auth response")
                key_url = urlparse(source_url)
                key_url = f"{key_url.scheme}://{key_url.netloc}/server_lookup.php?channel_id={channel_key}"
                key_response = await self._session.get(key_url, headers=self._headers(source_url))
                server_key = key_response.json().get("server_key")
                if not server_key:
                    raise ValueError("No server key found in response")
                if server_key == "top1/cdn":
                    server_url = f"https://top1.newkso.ru/top1/cdn/{channel_key}/mono.m3u8"
                else:
                    server_url = f"https://{server_key}new.newkso.ru/{server_key}/{channel_key}/mono.m3u8"
                m3u8 = await self._session.get(server_url, headers=self._headers(quote(str(source_url))))
                m3u8_data = ""
                for line in m3u8.text.split("\n"):
                    if line.startswith("#EXT-X-KEY:"):
                        original_url = re.search(r'URI="(.*?)"', line).group(1)
                        line = line.replace(original_url, f"{config.api_url}/key/{encrypt(original_url)}/{encrypt(urlparse(source_url).netloc)}")
                    elif line.startswith("http") and config.proxy_content:
                        line = f"{config.api_url}/content/{encrypt(line)}"
                    m3u8_data += line + "\n"
                return m3u8_data
        except Exception as e:
            logger.error(f"Error in stream method for channel {channel_id}: {str(e)}")
            raise

    # Semaphore for limiting concurrent stream requests
    _stream_semaphore = None
    
    async def _get_stream_semaphore(self):
        """Get or create stream semaphore"""
        if self._stream_semaphore is None:
            self._stream_semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent stream requests
        return self._stream_semaphore

    async def key(self, url: str, host: str):
        url = decrypt(url)
        host = decrypt(host)
        response = await self._session.get(url, headers=self._headers(f"{host}/", host), timeout=60)
        if response.status_code != 200:
            raise Exception(f"Failed to get key")
        return response.content

    @staticmethod
    def content_url(path: str):
        return decrypt(path)

    def playlist(self):
        data = "#EXTM3U\n"
        for channel in self.channels:
            entry = f" tvg-logo=\"{channel.logo}\",{channel.name}" if channel.logo else f",{channel.name}"
            data += f"#EXTINF:-1{entry}\n{config.api_url}/stream/{channel.id}.m3u8\n"
        return data

    async def schedule(self):
        response = await self._session.get(f"{self._base_url}/schedule/schedule-generated.php", headers=self._headers())
        return response.json()
