// ---------------------------------------------------------------------------
// Screen Share Helper — frontend logic
//
// Flow:
//   1. User clicks "Share screen"  -> getDisplayMedia, show video, connect WS.
//   2. A frame of the screen is captured every 2s (Gemini video max ~1fps, we
//      keep the latest and attach it to outgoing audio packets).
//   3. User clicks "Start talking"  -> capture mic, downsample to 16kHz PCM,
//      send audio + latest frame to the backend every ~1s.
//   4. Gemini replies with audio (played via AudioWorklet) + text transcript
//      (shown in the chat log).
// ---------------------------------------------------------------------------

const ROOT_PATH = window.ROOT_PATH || "";
const WS_PROTO = location.protocol === "https:" ? "wss" : "ws";
const WS_URL = `${WS_PROTO}://${location.host}${ROOT_PATH}/ws`;

const video = document.getElementById("videoElement");
const videoPlaceholder = document.getElementById("videoPlaceholder");
const canvas = document.getElementById("canvasElement");
const chatLog = document.getElementById("chatLog");
const statusEl = document.getElementById("status");

const shareButton = document.getElementById("shareButton");
const micButton = document.getElementById("micButton");
const stopButton = document.getElementById("stopButton");

let ctx2d = null;
let screenStream = null;
let micStream = null;
let webSocket = null;

let frameInterval = null;
let currentFrameB64 = null;

// Audio input (mic -> 16kHz PCM)
let micAudioContext = null;
let micProcessor = null;
let micSource = null;
let pcmChunks = [];
let sendInterval = null;

// Audio output (Gemini PCM -> speakers)
let playbackContext = null;
let workletNode = null;
let playbackReady = false;

let micActive = false;
let currentTurnText = "";

// ---------------------------------------------------------------------------
// Screen sharing
// ---------------------------------------------------------------------------

async function startScreenShare() {
    try {
        screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: { width: { max: 1280 }, height: { max: 720 } },
            audio: false,
        });

        video.srcObject = screenStream;
        videoPlaceholder.style.display = "none";

        await new Promise((resolve) => {
            video.onloadedmetadata = () => resolve();
        });

        // If the user stops sharing via the browser's native control, clean up.
        screenStream.getVideoTracks()[0].addEventListener("ended", stopEverything);

        ctx2d = canvas.getContext("2d");
        frameInterval = setInterval(captureFrame, 2000);

        connect();
        shareButton.disabled = true;
        micButton.disabled = false;
        stopButton.disabled = false;
    } catch (err) {
        console.error("Screen share error:", err);
        setStatus("Screen share cancelled");
    }
}

function captureFrame() {
    if (!screenStream || !ctx2d) return;
    if (!video.videoWidth || !video.videoHeight) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx2d.drawImage(video, 0, 0, canvas.width, canvas.height);
    currentFrameB64 = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

function connect() {
    setStatus("Connecting...");
    webSocket = new WebSocket(WS_URL);

    webSocket.onopen = () => setStatus("Connected — share is live");
    webSocket.onmessage = receiveMessage;
    webSocket.onerror = () => setStatus("Connection error");
    webSocket.onclose = () => setStatus("Disconnected");
}

function receiveMessage(event) {
    const msg = JSON.parse(event.data);

    if (msg.text) {
        currentTurnText += msg.text;
        renderCurrentTurn(currentTurnText);
    }
    if (msg.audio) {
        playAudioChunk(msg.audio);
    }
    if (msg.turn_complete) {
        currentTurnText = "";
        currentTurnEl = null; // next transcript starts a new bubble
    }
}

function sendMedia(b64PCM) {
    if (!webSocket || webSocket.readyState !== WebSocket.OPEN) return;

    const mediaChunks = [{ mime_type: "audio/pcm", data: b64PCM }];
    if (currentFrameB64) {
        mediaChunks.push({ mime_type: "image/jpeg", data: currentFrameB64 });
    }

    webSocket.send(JSON.stringify({ realtime_input: { media_chunks: mediaChunks } }));
}

// ---------------------------------------------------------------------------
// Microphone capture -> 16kHz PCM
// ---------------------------------------------------------------------------

async function startMic() {
    micStream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });

    // Use a 16kHz context so getChannelData already matches Gemini's expected rate.
    micAudioContext = new AudioContext({ sampleRate: 16000 });
    micSource = micAudioContext.createMediaStreamSource(micStream);
    micProcessor = micAudioContext.createScriptProcessor(4096, 1, 1);

    micProcessor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);
        const pcm16 = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        pcmChunks.push(...pcm16);
    };

    micSource.connect(micProcessor);
    micProcessor.connect(micAudioContext.destination);

    sendInterval = setInterval(flushPcm, 1000);

    micActive = true;
    micButton.textContent = "Listening…";
    micButton.classList.add("active");
    setStatus("Listening — speak now");
}

function flushPcm() {
    if (pcmChunks.length === 0) return;

    const buffer = new ArrayBuffer(pcmChunks.length * 2);
    const view = new DataView(buffer);
    pcmChunks.forEach((value, i) => view.setInt16(i * 2, value, true));

    // Base64-encode in chunks to avoid call-stack limits on large buffers.
    const bytes = new Uint8Array(buffer);
    let binary = "";
    const CHUNK = 0x8000;
    for (let i = 0; i < bytes.length; i += CHUNK) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
    }
    sendMedia(btoa(binary));
    pcmChunks = [];
}

function stopMic() {
    if (sendInterval) clearInterval(sendInterval);
    if (micProcessor) micProcessor.disconnect();
    if (micSource) micSource.disconnect();
    if (micAudioContext) micAudioContext.close();
    if (micStream) micStream.getTracks().forEach((t) => t.stop());

    pcmChunks = [];
    micActive = false;
    micButton.textContent = "Start talking";
    micButton.classList.remove("active");
    setStatus("Paused — click Start talking to resume");
}

function toggleMic() {
    if (micActive) {
        stopMic();
    } else {
        initPlayback().then(startMic).catch((err) => {
            console.error("Mic error:", err);
            setStatus("Microphone unavailable");
        });
    }
}

// ---------------------------------------------------------------------------
// Audio playback (Gemini -> speakers)
// ---------------------------------------------------------------------------

async function initPlayback() {
    if (playbackReady) return;
    playbackContext = new AudioContext({ sampleRate: 24000 });
    await playbackContext.audioWorklet.addModule(`${ROOT_PATH}/static/pcm-processor.js`);
    workletNode = new AudioWorkletNode(playbackContext, "pcm-processor");
    workletNode.connect(playbackContext.destination);
    playbackReady = true;
}

function base64ToInt16(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return new Int16Array(bytes.buffer);
}

async function playAudioChunk(base64Audio) {
    try {
        if (!playbackReady) await initPlayback();
        if (playbackContext.state === "suspended") await playbackContext.resume();

        const int16 = base64ToInt16(base64Audio);
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

        workletNode.port.postMessage(float32);
    } catch (err) {
        console.error("Playback error:", err);
    }
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

function setStatus(text) {
    statusEl.textContent = text;
}

let currentTurnEl = null;
function renderCurrentTurn(text) {
    const hint = chatLog.querySelector(".hint");
    if (hint) hint.remove();

    if (!currentTurnEl) {
        currentTurnEl = document.createElement("div");
        currentTurnEl.className = "msg assistant";
        chatLog.appendChild(currentTurnEl);
    }
    currentTurnEl.textContent = text;
    chatLog.scrollTop = chatLog.scrollHeight;
}

function stopEverything() {
    stopMic();
    if (frameInterval) clearInterval(frameInterval);
    if (screenStream) screenStream.getTracks().forEach((t) => t.stop());
    if (webSocket) webSocket.close();

    video.srcObject = null;
    videoPlaceholder.style.display = "flex";
    shareButton.disabled = false;
    micButton.disabled = true;
    stopButton.disabled = true;
    setStatus("Stopped");
}

shareButton.addEventListener("click", startScreenShare);
micButton.addEventListener("click", toggleMic);
stopButton.addEventListener("click", stopEverything);