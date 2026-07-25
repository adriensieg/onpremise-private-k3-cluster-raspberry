from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from itertools import count

app = FastAPI(root_path="/clotilde")

app.mount("/static", StaticFiles(directory="static"), name="static")

notes: dict[int, dict] = {}
ids = count(1)


class NoteIn(BaseModel):
    title: str
    body: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/notes")
def list_notes():
    return list(notes.values())


@app.post("/api/notes")
def create_note(note: NoteIn):
    nid = next(ids)
    notes[nid] = {"id": nid, **note.model_dump()}
    return notes[nid]


@app.put("/api/notes/{nid}")
def update_note(nid: int, note: NoteIn):
    if nid not in notes:
        raise HTTPException(404, "not found")
    notes[nid] = {"id": nid, **note.model_dump()}
    return notes[nid]


@app.delete("/api/notes/{nid}")
def delete_note(nid: int):
    if nid not in notes:
        raise HTTPException(404, "not found")
    return notes.pop(nid)


@app.get("/")
def index():
    return FileResponse("static/index.html")