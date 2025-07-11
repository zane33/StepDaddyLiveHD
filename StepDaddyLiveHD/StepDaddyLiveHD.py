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
            # Load channels from backend
            channels = backend.get_channels()
            
            if not channels:
                self.connection_status = "error"
                self.error_message = "No channels available. Please try again later."
                return
                
            self.channels = channels
            self.channels_count = len(self.channels)
            self.connection_status = "connected"
            self.last_update = time.strftime("%H:%M:%S")
            
            # Save to fallback if successful
            if self.channels:
                import json
                import os
                fallback_data = [
                    {
                        "id": ch.id,
                        "name": ch.name,
                        "logo": ch.logo,
                        "tags": ch.tags,
                        "is_live": getattr(ch, 'is_live', True)
                    }
                    for ch in self.channels  # Save all channels as fallback
                ]
                os.makedirs("StepDaddyLiveHD", exist_ok=True)
                with open("StepDaddyLiveHD/fallback_channels.json", "w") as f:
                    json.dump(fallback_data, f, indent=2)
                    
        except Exception as e:
            self.connection_status = "error"
            self.error_message = f"Error loading channels: {str(e)}"
            # Try to load from fallback
            try:
                import json
                import os
                if os.path.exists("StepDaddyLiveHD/fallback_channels.json"):
                    with open("StepDaddyLiveHD/fallback_channels.json", "r") as f:
                        fallback_data = json.load(f)
                        self.channels = [Channel(**channel_data) for channel_data in fallback_data]
                        self.channels_count = len(self.channels)
                        self.last_update = "from cache"
                        if self.channels:
                            self.connection_status = "connected"
                            self.error_message = "Using cached data - some features may be limited"
            except Exception as fallback_error:
                self.error_message = f"Failed to load channels (both live and cached): {str(fallback_error)}"
        
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
    def on_load(self):
        """Initial load when page loads."""
        return self.load_channels

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
        position="sticky",
        top="0",
        z_index="10",
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
            State.is_loading & (State.channels_count == 0),
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
        navbar(search_bar()),
        status_bar(),
        channels_grid(),
        width="100%",
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
