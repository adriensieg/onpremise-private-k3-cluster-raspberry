from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from K3s on Raspberry Pi", "host": os.uname().nodename}

@app.get("/")
def index():
    return FileResponse("static/index.html")
# trigger

# trigger
