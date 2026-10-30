#!/usr/bin/env python3
"""FastAPI backend for ProjWT — exposes gesture control + vehicle commands as API."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import ProjWT modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projwt" / "src"))

from gesture_control_PWT import GestureController, COMMAND_MENU
from vehicle_actuator_PWT import make_actuator, KNOWN_COMMANDS

# ------- Models -------

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    ok: bool
    command: str
    timestamp: str
    state: str = "IDLE"
    error: str = None

class BiometricData(BaseModel):
    heart_rate: int
    timestamp: str
    battery: int = None

# ------- FastAPI app -------

app = FastAPI(
    title="ProjWT API",
    description="Vehicle control via gesture recognition + biometric dashboard",
    version="1.0.0"
)

# CORS for web/mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
gesture_controller = None
connected_websockets = set()

# ------- Initialization -------

def init_controller():
    """Initialize the gesture controller with mock actuator (can be overridden)."""
    global gesture_controller

    backend = os.getenv("PROJWT_BACKEND", "mock")
    print(f"[ProjWT] Initializing with backend: {backend}")

    actuator = make_actuator(backend)
    gesture_controller = GestureController(actuator, arm_timeout=12.0)

    return gesture_controller

@app.on_event("startup")
async def startup():
    print("[ProjWT] Starting backend server...")
    init_controller()

# ------- HTTP Endpoints -------

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "controller_ready": gesture_controller is not None
    }

@app.get("/commands")
async def list_commands():
    """List all available vehicle commands."""
    return {
        "commands": list(KNOWN_COMMANDS),
        "menu": COMMAND_MENU
    }

@app.get("/state")
async def get_state():
    """Get current FSM state."""
    if not gesture_controller:
        return {"error": "Controller not initialized"}

    state_name = gesture_controller.fsm.state
    return {
        "state": state_name,
        "armed": state_name != "IDLE",
        "selected_command": COMMAND_MENU[gesture_controller.sel] if gesture_controller.sel < len(COMMAND_MENU) else None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/command")
async def send_command(req: CommandRequest) -> CommandResponse:
    """Send a vehicle command (lock, unlock, flash, etc.)."""
    if not gesture_controller:
        return CommandResponse(
            ok=False, command=req.command, timestamp=datetime.utcnow().isoformat(),
            error="Controller not initialized"
        )

    # Dispatch through the gesture controller's actuator
    result = gesture_controller.act.dispatch(req.command)

    return CommandResponse(
        ok=result.get("ok", False),
        command=req.command,
        timestamp=datetime.utcnow().isoformat(),
        state=gesture_controller.fsm.state,
        error=result.get("error")
    )

@app.post("/gesture/arm")
async def arm_gesture():
    """Manually trigger ARM gesture (debug/mobile)."""
    if not gesture_controller:
        return {"error": "Controller not initialized"}

    t = asyncio.get_event_loop().time()
    gesture_controller.band_double_flick(t)

    return {
        "state": gesture_controller.fsm.state,
        "armed": gesture_controller.fsm.state != "IDLE"
    }

@app.post("/gesture/panic")
async def panic_gesture():
    """Manually trigger PANIC gesture (emergency disarm)."""
    if not gesture_controller:
        return {"error": "Controller not initialized"}

    t = asyncio.get_event_loop().time()
    gesture_controller.band_shake(t)

    return {
        "state": gesture_controller.fsm.state,
        "armed": gesture_controller.fsm.state != "IDLE"
    }

# ------- WebSocket for live biometrics -------

class BiometricManager:
    """Simulates live biometric streaming (heart rate ~1 Hz)."""

    def __init__(self):
        self.hr = 72
        self.battery = 85

    async def stream_biometrics(self, interval=1.0):
        """Generate synthetic biometric data (HR varies ±5 bpm randomly)."""
        import random
        while True:
            self.hr = max(60, min(120, self.hr + random.randint(-5, 5)))
            self.battery = max(0, self.battery - 0.1)

            yield {
                "heart_rate": self.hr,
                "battery": int(self.battery),
                "timestamp": datetime.utcnow().isoformat()
            }
            await asyncio.sleep(interval)

bio_mgr = BiometricManager()

@app.websocket("/ws/biometrics")
async def websocket_biometrics(websocket: WebSocket):
    """WebSocket stream of live biometrics (heart rate, battery)."""
    await websocket.accept()
    connected_websockets.add(websocket)

    try:
        gen = bio_mgr.stream_biometrics(interval=1.0)
        while True:
            data = await gen.__anext__()
            await websocket.send_json(data)

            # Also listen for client messages (e.g., "pause", "resume")
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                if msg == "stop":
                    break
            except asyncio.TimeoutError:
                pass  # No message, continue streaming

    except WebSocketDisconnect:
        pass
    finally:
        connected_websockets.discard(websocket)

# ------- Main -------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
