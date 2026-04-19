import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import db
from patientzero.config.settings import AVAILABLE_MODELS
from patientzero.db.queries.sessions import (
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
from patientzero.llm.factory import parse_provider_model

router = APIRouter()


class CreateSessionRequest(BaseModel):
    model: str = "mock:default"


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=10000)


class UpdateSessionRequest(BaseModel):
    model: str


@router.get("/models")
async def get_available_models():
    return AVAILABLE_MODELS


@router.post("/sessions")
async def create_new_session(request: CreateSessionRequest):
    session = await create_session(db, request.model)
    return session.to_dict()


@router.get("/sessions")
async def get_all_sessions():
    sessions = await list_sessions(db)
    return [s.to_dict() for s in sessions]


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    turns = await get_turns(db, session_id)
    return {**session.to_dict(), "turns": [t.to_dict() for t in turns]}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await update_session_model(db, session_id, request.model)
    updated = await get_session(db, session_id)
    return updated.to_dict()


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await delete_session(db, session_id)
    return {"ok": True}


@router.post("/chat")
async def chat(request: ChatRequest):
    session = await get_session(db, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turn_number = await get_turn_count(db, request.session_id)
    await create_turn(db, request.session_id, "user", request.message, turn_number)

    if turn_number == 0:
        title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        await update_session_title(db, request.session_id, title)

    turns = await get_turns(db, request.session_id)
    messages = [{"role": t.role, "content": t.content} for t in turns]

    provider, model = parse_provider_model(session.model)

    async def generate():
        full_response = ""
        try:
            async for chunk in provider.stream(messages, model):
                full_response += chunk
                yield {"data": json.dumps({"token": chunk})}
            await create_turn(db, request.session_id, "assistant", full_response, turn_number + 1)
            yield {"event": "done", "data": ""}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(generate())
