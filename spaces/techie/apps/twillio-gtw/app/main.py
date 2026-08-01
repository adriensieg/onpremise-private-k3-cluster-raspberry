import json
import logging
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Header
from fastapi.responses import Response
from google import genai
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from .lib.config import (
    PORT, APP_BASE_URL, GOOGLE_API_KEY,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    API_KEY, TECHNICIAN_PHONE,
)
from .lib.prompts import build_technician_system_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("techie-gtw")

gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
logger.info("Clients initialised. Technician: %s", TECHNICIAN_PHONE)

call_contexts: dict = {}

app = FastAPI(title="Techie Twilio Gateway")


def _require_api_key(authorization: Optional[str]):
    """Simple bearer-token gate. If API_KEY is unset, auth is disabled."""
    if not API_KEY:
        return
    expected = f"Bearer {API_KEY}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/call")
async def trigger_call(request: Request, authorization: Optional[str] = Header(None)):
    """Immediately place an outbound call to the technician using the payload."""
    _require_api_key(authorization)

    payload = await request.json()
    logger.info("[CALL] Received dispatch request: %s", payload)

    twiml_url = f"{APP_BASE_URL}/twiml"
    try:
        call = twilio_client.calls.create(
            to=TECHNICIAN_PHONE,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
            method="POST",
        )
    except TwilioRestException as exc:
        logger.exception("[CALL] Twilio error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Twilio error: {exc}")

    call_contexts[call.sid] = {"payload": payload}
    logger.info("[CALL] Outbound call created. CallSid=%s", call.sid)

    return {
        "status": "call_initiated",
        "call_sid": call.sid,
        "technician_phone": TECHNICIAN_PHONE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/twiml")
async def twiml_endpoint(request: Request):
    ws_url = (
        APP_BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws"
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <ConversationRelay
      url="{ws_url}"
      welcomeGreeting="Hello, this is an automated assistant calling on behalf of a restaurant. Please hold one moment."
      ttsProvider="Google"
      voice="en-US-Journey-O"
    />
  </Connect>
</Response>"""
    return Response(content=xml, media_type="text/xml")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    call_sid: Optional[str] = None
    chat = None

    try:
        while True:
            message = json.loads(await websocket.receive_text())
            mtype = message.get("type")

            if mtype == "setup":
                call_sid = message.get("callSid")
                ctx = call_contexts.get(call_sid, {})
                payload = ctx.get("payload", {})
                chat = gemini_client.chats.create(
                    model="gemini-2.5-flash",
                    config={"system_instruction": build_technician_system_prompt(payload)},
                )
                opening = chat.send_message(
                    "Start the call now. Greet the technician and explain the issue."
                )
                await websocket.send_text(json.dumps(
                    {"type": "text", "token": opening.text, "last": True}
                ))

            elif mtype == "prompt":
                if chat is None:
                    continue
                try:
                    reply = chat.send_message(message.get("voicePrompt", "")).text
                except Exception as exc:
                    logger.exception("[WS] Gemini error: %s", exc)
                    reply = "I'm sorry, I hit a technical issue. Please call the restaurant directly. Goodbye."
                await websocket.send_text(json.dumps(
                    {"type": "text", "token": reply, "last": True}
                ))

            elif mtype == "end":
                break

    except WebSocketDisconnect:
        logger.info("[WS] Disconnected. CallSid=%s", call_sid)
    finally:
        call_contexts.pop(call_sid, None)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_calls": len(call_contexts),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")