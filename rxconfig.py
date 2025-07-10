import reflex as rx
import os


proxy_content = os.environ.get("PROXY_CONTENT", "TRUE").upper() == "TRUE"
socks5 = os.environ.get("SOCKS5", "")
port = os.environ.get("PORT", "3232")
backend_port = int(os.environ.get("BACKEND_PORT", "8005"))
backend_host_uri = os.environ.get("BACKEND_HOST_URI", "http://localhost:8005")
api_url = os.environ.get("API_URL", "http://localhost:3232")
reflex_api_url = os.environ.get("REFLEX_API_URL", "http://localhost:8005")
daddylive_uri = os.environ.get("DADDYLIVE_URI", "https://thedaddy.click")

print(f"PROXY_CONTENT: {proxy_content}")
print(f"SOCKS5: {socks5}")
print(f"PORT: {port}")
print(f"BACKEND_PORT: {backend_port}")
print(f"REFLEX_API_URL: {reflex_api_url}")
print(f"BACKEND_HOST_URI: {backend_host_uri}")
print(f"API_URL: {api_url}")
print(f"DADDYLIVE_URI: {daddylive_uri}")

config = rx.Config(
    app_name="StepDaddyLiveHD",
    proxy_content=proxy_content,
    socks5=socks5,
    show_built_with_reflex=False,
    backend_port=backend_port,  # Use BACKEND_PORT environment variable
    backend_host_uri=reflex_api_url,  # Use REFLEX_API_URL for backend communication
    api_url=api_url,  # Frontend API URL for stream endpoints
    daddylive_uri=daddylive_uri,  # Allow custom daddylive endpoint URI
    env=rx.Env.PROD,  # Set to production to prevent runtime compilation
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
