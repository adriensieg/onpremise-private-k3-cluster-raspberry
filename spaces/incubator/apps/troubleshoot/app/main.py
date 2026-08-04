"""
Screen Share Helper — FastAPI backend.

Serves the frontend and proxies a browser WebSocket to the Gemini Live API.
The browser streams microphone audio + periodic screen-share frames; Gemini
streams back audio (spoken guidance) plus a text transcription of what it says.

Run:
    pip install -r requirements.txt
    export GOOGLE_API_KEY="your-key"      # get one at https://aistudio.google.com/apikey
    python main.py
Then open http://localhost:8000
"""

import asyncio
import base64
import json
import os
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from google import genai
from google.genai import types

# --- Configuration -----------------------------------------------------------

MODEL = "gemini-3.1-flash-live-preview"  # current Live-capable model

SYSTEM_INSTRUCTION = (
    "You are a friendly, patient screen-sharing support assistant. The user is "
    "sharing their screen because they are stuck using a piece of software and "
    "need step-by-step help. Your job:\n"
    "1) Look carefully at what is on screen right now.\n"
    "2) Tell the user exactly what to do next — which button, menu, or field to "
    "click, in plain language (e.g. 'click the blue Save button at the top right').\n"
    "3) Give ONE step at a time, then wait. Don't dump a long list.\n"
    "4) If you can't see something clearly, ask them to scroll or point to it.\n"
    "5) Keep responses short, spoken-friendly, and encouraging."
)

# The API key is read automatically from the GOOGLE_API_KEY env var by the SDK.
client = genai.Client(http_options={"api_version": "v1beta"})

# URL prefix the app is served under (e.g. "/troubleshoot" in production,
# "" for local dev). Set via env var in the k8s deployment.
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# --- Routes ------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"root_path": ROOT_PATH}
    )


@app.websocket("/ws")
async def websocket_endpoint(client_ws: WebSocket):
    """Bridge one browser connection to one Gemini Live session."""
    await client_ws.accept()
    print("Browser connected")

    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": SYSTEM_INSTRUCTION,
        # Ask Gemini to also return a text transcript of its spoken answer,
        # so we can show it in the chat log.
        "output_audio_transcription": {},
    }

    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini Live API")

            async def browser_to_gemini():
                """Forward mic audio + screen frames from browser to Gemini."""
                try:
                    while True:
                        raw = await client_ws.receive_text()
                        data = json.loads(raw)
                        chunks = data.get("realtime_input", {}).get("media_chunks", [])
                        for chunk in chunks:
                            mime = chunk.get("mime_type", "")
                            payload = base64.b64decode(chunk["data"])
                            if mime.startswith("audio/pcm"):
                                await session.send_realtime_input(
                                    audio=types.Blob(
                                        data=payload,
                                        mime_type="audio/pcm;rate=16000",
                                    )
                                )
                            elif mime.startswith("image/jpeg"):
                                await session.send_realtime_input(
                                    video=types.Blob(
                                        data=payload,
                                        mime_type="image/jpeg",
                                    )
                                )
                except WebSocketDisconnect:
                    print("Browser disconnected (send loop)")
                except Exception as e:
                    print(f"browser_to_gemini error: {e}")
                    traceback.print_exc()

            async def gemini_to_browser():
                """Forward Gemini's audio + transcript back to the browser."""
                try:
                    while True:
                        async for response in session.receive():
                            server_content = response.server_content
                            if server_content is None:
                                continue

                            # Spoken-answer transcript (text)
                            transcription = server_content.output_transcription
                            if transcription and transcription.text:
                                await client_ws.send_text(
                                    json.dumps({"text": transcription.text})
                                )

                            # Audio chunks
                            model_turn = server_content.model_turn
                            if model_turn:
                                for part in model_turn.parts:
                                    inline = getattr(part, "inline_data", None)
                                    if inline and inline.data:
                                        b64 = base64.b64encode(inline.data).decode("utf-8")
                                        await client_ws.send_text(
                                            json.dumps({"audio": b64})
                                        )

                            if server_content.turn_complete:
                                await client_ws.send_text(
                                    json.dumps({"turn_complete": True})
                                )
                except WebSocketDisconnect:
                    print("Browser disconnected (receive loop)")
                except Exception as e:
                    print(f"gemini_to_browser error: {e}")
                    traceback.print_exc()

            await asyncio.gather(browser_to_gemini(), gemini_to_browser())

    except Exception as e:
        print(f"Session error: {e}")
        traceback.print_exc()
    finally:
        print("Gemini session closed")


if __name__ == "__main__":
    import uvicorn

    if not os.environ.get("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY is not set. Get one at "
              "https://aistudio.google.com/apikey")
    uvicorn.run(app, host="0.0.0.0", port=8000)