import reflex as rx
import asyncio
import time
from typing import List, Optional
import StepDaddyLiveHD.pages
from StepDaddyLiveHD import backend
from StepDaddyLiveHD.components import navbar, card
from StepDaddyLiveHD.step_daddy import Channel


class State(rx.State):
    """Main application state with real-time features."""
    
    # Channel data
    channels: List[Channel] = []
    search_query: str = ""
    
    # Real-time status
    is_loading: bool = True  # Start with loading state
    last_update: str = ""
    connection_status: str = "connecting"
    channels_count: int = 0
    filtered_channels_count: int = 0
    error_message: str = ""  # Track error messages
    
    # Live updates
    auto_refresh: bool = True
    refresh_interval: int = 300  # 5 minutes
    
    # WebSocket state
    ws_connected: bool = False
    
    # UI state
    status_bar_visible: bool = True
    
    @rx.var
    def filtered_channels(self) -> List[Channel]:
        """Filter channels based on search query."""
        if not self.search_query:
            filtered = self.channels
        else:
            filtered = [ch for ch in self.channels if self.search_query.lower() in ch.name.lower()]
        self.filtered_channels_count = len(filtered)
        return filtered
    
    @rx.var
    def status_color(self) -> str:
        """Get color for connection status indicator."""
        if not self.ws_connected:
            return "red"
        if self.connection_status == "connected":
            return "green"
        elif self.connection_status == "connecting":
            return "yellow"
        else:
            return "red"
    
    @rx.var
    def status_text(self) -> str:
        """Get formatted status text."""
        if not self.ws_connected:
            return "WebSocket disconnected - trying to reconnect..."
        if self.connection_status == "connected":
            if self.last_update == "from fallback":
                return f"Connected • {self.channels_count} channels • Fallback data loaded"
            elif self.last_update == "fallback mode":
                return f"Connected • {self.channels_count} channels • Demo mode active"
            else:
                return f"Connected • {self.channels_count} channels • Updated {self.last_update}"
        elif self.connection_status == "connecting":
            return "Connecting to server..."
        else:
            return f"Connection failed{' • ' + self.error_message if self.error_message else ''}"
    
    async def load_channels(self):
        """Load channels from backend with real-time updates."""
        self.is_loading = True
        self.connection_status = "connecting"
        self.error_message = ""
        
        try:
            # First try to fetch from the API endpoint
            import httpx
            import json
            import os
            
            try:
                # Try to connect to the API endpoint through proxy
                frontend_port = os.environ.get("PORT", "3232")
                api_url = f"http://localhost:{frontend_port}"
                async with httpx.AsyncClient(timeout=10.0, base_url=api_url) as client:
                    response = await client.get("/api/channels")
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("channels"):
                            self.channels = [Channel(**channel_data) for channel_data in data["channels"]]
                            self.channels_count = len(self.channels)
                            self.connection_status = "connected"
                            self.ws_connected = True
                            self.last_update = time.strftime("%H:%M:%S")
                            self.error_message = ""
                            self.is_loading = False
                            return
                        else:
                            raise Exception("No channels in API response")
                    else:
                        raise Exception(f"API returned status {response.status_code}")
            except Exception as api_error:
                print(f"API error: {api_error}")
                # Fall back to direct backend call if API is not available
                try:
                    channels = backend.get_channels()
                    if channels:
                        self.channels = channels
                        self.channels_count = len(self.channels)
                        self.connection_status = "connected"
                        self.ws_connected = True
                        self.last_update = time.strftime("%H:%M:%S")
                        self.error_message = ""
                        self.is_loading = False
                        return
                    else:
                        raise Exception("No channels returned from backend")
                except Exception as backend_error:
                    print(f"Backend error: {backend_error}")
                    # Try to load from fallback file
                    fallback_path = "StepDaddyLiveHD/fallback_channels.json"
                    if os.path.exists(fallback_path):
                        with open(fallback_path, "r") as f:
                            fallback_data = json.load(f)
                            self.channels = [Channel(**channel_data) for channel_data in fallback_data]
                            self.channels_count = len(self.channels)
                            self.connection_status = "connected"
                            self.ws_connected = True
                            self.last_update = "from fallback"
                            self.error_message = "Using fallback data - backend unavailable"
                            self.is_loading = False
                            return
                    else:
                        # Last resort: create minimal demo channels
                        self.channels = [
                            Channel(id="1", name="ESPN", logo="/missing.png", tags=["sports"]),
                            Channel(id="2", name="CNN", logo="/missing.png", tags=["news"]),
                            Channel(id="3", name="HBO", logo="/missing.png", tags=["entertainment"]),
                            Channel(id="4", name="Discovery Channel", logo="/missing.png", tags=["documentary"]),
                            Channel(id="5", name="National Geographic", logo="/missing.png", tags=["documentary", "nature"])
                        ]
                        self.channels_count = len(self.channels)
                        self.connection_status = "connected"
                        self.ws_connected = True
                        self.last_update = "demo mode"
                        self.error_message = "Backend unavailable, using demo channels"
                
        except Exception as e:
            self.connection_status = "error"
            self.error_message = f"Critical error: {str(e)}"
            self.channels = []
            self.channels_count = 0
            self.ws_connected = False
        
        finally:
            self.is_loading = False
    
    @rx.event
    def handle_websocket_connect(self):
        """Handle WebSocket connection."""
        self.ws_connected = True
        return self.load_channels
    
    @rx.event
    def handle_websocket_disconnect(self):
        """Handle WebSocket disconnection."""
        self.ws_connected = False
        self.connection_status = "error"
        self.error_message = "WebSocket disconnected"
    
    @rx.event
    def handle_websocket_error(self, error: str):
        """Handle WebSocket error."""
        self.connection_status = "error"
        self.error_message = f"WebSocket error: {error}"
    
    @rx.event
    def refresh_channels(self):
        """Manually refresh channels."""
        return self.load_channels
    
    @rx.event
    def toggle_auto_refresh(self):
        """Toggle automatic refresh."""
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            # Start background refresh
            return self.start_background_refresh
    
    async def start_background_refresh(self):
        """Start background refresh task."""
        while self.auto_refresh and self.ws_connected:
            await asyncio.sleep(self.refresh_interval)
            if self.auto_refresh and self.ws_connected:  # Check again in case it was disabled
                await self.load_channels()
    
    @rx.event
    def search_channels(self, query: str):
        """Handle search with real-time filtering."""
        self.search_query = query
    
    @rx.event
    def show_status_bar(self):
        """Show status bar on hover."""
        self.status_bar_visible = True
    
    @rx.event  
    def hide_status_bar(self):
        """Hide status bar when not hovering."""
        self.status_bar_visible = False
    
    @rx.event
    def on_load(self):
        """Initial load when page loads."""
        # Set WebSocket as connected since Reflex manages the connection
        self.ws_connected = True
        self.connection_status = "connecting"
        # Hide status bar after initial load
        self.status_bar_visible = False
        # Return the async load_channels method to trigger state update
        return State.load_channels

    async def handle_channel_update(self):
        """Handle real-time channel updates."""
        try:
            await self.load_channels()
            if self.auto_refresh:
                # Schedule next update
                await asyncio.sleep(self.refresh_interval)
                return State.handle_channel_update
        except Exception as e:
            self.connection_status = "error"
            self.error_message = str(e)
            # Don't raise the exception - just log it and continue
            print(f"Channel update error: {str(e)}")
            # Retry after error with backoff
            await asyncio.sleep(min(self.refresh_interval * 2, 600))  # Max 10 minute backoff
            return State.handle_channel_update


def status_bar() -> rx.Component:
    """Real-time status bar component."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background_color=State.status_color,
                ),
                rx.text(
                    State.status_text,
                    size="2",
                    color="gray",
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Refresh",
                    on_click=State.refresh_channels,
                    loading=State.is_loading,
                    size="2",
                    variant="soft",
                ),
                rx.button(
                    rx.cond(
                        State.auto_refresh,
                        rx.icon("pause", size=16),
                        rx.icon("play", size=16),
                    ),
                    rx.cond(
                        State.auto_refresh,
                        "Auto-refresh ON",
                        "Auto-refresh OFF",
                    ),
                    on_click=State.toggle_auto_refresh,
                    size="2",
                    variant=rx.cond(State.auto_refresh, "solid", "outline"),
                    color_scheme=rx.cond(State.auto_refresh, "green", "gray"),
                ),
                spacing="2",
            ),
            justify="between",
            width="100%",
        ),
        padding="1rem",
        border_bottom="1px solid var(--gray-6)",
        background_color="var(--gray-2)",
        position="fixed",
        top=rx.cond(State.status_bar_visible, "0", "-100px"),
        left="0",
        right="0",
        z_index="100",
        transition="top 0.3s ease-in-out",
        on_mouse_enter=State.show_status_bar,
        on_mouse_leave=State.hide_status_bar,
    )


def search_bar() -> rx.Component:
    """Enhanced search bar with real-time search."""
    return rx.box(
        rx.input(
            rx.input.slot(
                rx.icon("search"),
            ),
            placeholder="Search channels in real-time...",
            on_change=State.search_channels,
            value=State.search_query,
            width="100%",
            max_width="25rem",
            size="3",
        ),
        padding="1rem",
    )


def channels_grid() -> rx.Component:
    """Channels grid with loading states."""
    return rx.center(
        rx.cond(
            State.is_loading,
            rx.vstack(
                rx.spinner(size="3"),
                rx.text("Loading channels...", size="2", color="gray"),
                spacing="4",
                align="center",
            ),
            rx.cond(
                State.filtered_channels_count > 0,
                rx.vstack(
                    rx.text(
                        rx.cond(
                            State.search_query != "",
                            f"Found {State.filtered_channels_count} channels matching '{State.search_query}'",
                            f"Showing {State.filtered_channels_count} channels",
                        ),
                        size="2",
                        color="gray",
                        align="center",
                    ),
                    rx.grid(
                        rx.foreach(
                            State.filtered_channels,
                            lambda channel: card(channel),
                        ),
                        grid_template_columns="repeat(auto-fill, minmax(250px, 1fr))",
                        spacing=rx.breakpoints(
                            initial="4",
                            sm="6",
                            lg="9"
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.vstack(
                    rx.icon("tv", size=48, color="gray"),
                    rx.text(
                        rx.cond(
                            State.search_query != "",
                            f"No channels found matching '{State.search_query}'",
                            "No channels available",
                        ),
                        size="4",
                        color="gray",
                        weight="medium",
                    ),
                    rx.text(
                        rx.cond(
                            State.search_query != "",
                            "Try a different search term",
                            "Check your connection and try refreshing",
                        ),
                        size="2",
                        color="gray",
                    ),
                    spacing="4",
                    align="center",
                ),
            ),
        ),
        padding="1rem",
        min_height="50vh",
    )


@rx.page("/", on_load=State.on_load)
def index() -> rx.Component:
    """Main page with real-time features."""
    return rx.box(
        # Top trigger area for auto-hide status bar
        rx.box(
            height="20px",
            width="100%",
            position="fixed",
            top="0",
            left="0",
            z_index="99",
            on_mouse_enter=State.show_status_bar,
        ),
        navbar(search_bar()),
        status_bar(),
        channels_grid(),
        width="100%",
        # Add top padding to account for fixed status bar
        padding_top="120px",
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="red",
    ),
    api_transformer=backend.fastapi_app,
)

# Register the background channel update task
app.register_lifespan_task(backend.update_channels)
