import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import db
from core.config.settings import AVAILABLE_MODELS
from core.db.queries.sessions import (
    create_session,
    create_turn,
    delete_session,
    get_session,
    get_turn_count,
    get_turns,
    list_sessions,
    update_session_model,
    update_session_title,
)
from core.llm.factory import parse_provider_model

router = APIRouter()


class CreateSessionRequest(BaseModel):
    model: str = "mock:default"


class ChatRequest(BaseModel):
    session_id: str
    message: str


class UpdateSessionRequest(BaseModel):
    model: str


@router.get("/models")
def get_available_models():
    return AVAILABLE_MODELS


@router.post("/sessions")
def create_new_session(request: CreateSessionRequest):
    return create_session(db, request.model).to_dict()


@router.get("/sessions")
def get_all_sessions():
    return [s.to_dict() for s in list_sessions(db)]


@router.get("/sessions/{session_id}")
def get_session_detail(session_id: str):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    turns = get_turns(db, session_id)
    return {**session.to_dict(), "turns": [t.to_dict() for t in turns]}


@router.patch("/sessions/{session_id}")
def update_session(session_id: str, request: UpdateSessionRequest):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_session_model(db, session_id, request.model)
    return get_session(db, session_id).to_dict()


@router.delete("/sessions/{session_id}")
def delete_session_endpoint(session_id: str):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(db, session_id)
    return {"ok": True}


@router.post("/chat")
async def chat(request: ChatRequest):
    session = get_session(db, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turn_number = get_turn_count(db, request.session_id)
    create_turn(db, request.session_id, "user", request.message, turn_number)

    if turn_number == 0:
        title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        update_session_title(db, request.session_id, title)

    turns = get_turns(db, request.session_id)
    messages = [{"role": t.role, "content": t.content} for t in turns]

    provider, model = parse_provider_model(session.model)

    async def generate():
        full_response = ""
        async for chunk in provider.stream(messages, model):
            full_response += chunk
            yield {"data": json.dumps({"token": chunk})}
        create_turn(db, request.session_id, "assistant", full_response, turn_number + 1)
        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())
