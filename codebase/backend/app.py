import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from config import config
from schemas import (
    ExplainRequest, ExplainResponse, RelatedConcept,
    SessionCreate, SessionPatch, SessionResponse,
    SavedTerm, SavedTermCreate, SavedTermListResponse,
    ChatRequest, ChatResponse, HealthResponse
)
from llm_client import llm_client
from sessions import session_manager

app = FastAPI(
    title="VLearn AI Tutor & Glossary API",
    description="Backend AI Tutor giải thích thuật ngữ AI theo ngữ cảnh và quản lý thẻ ôn tập cho VLearn",
    version="1.0.0"
)

# Cho phép CORS để Web Extension và Frontend HTML giao tiếp được với Backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="healthy",
        groq_available=bool(config.GROQ_API_KEY),
        gemini_available=bool(config.GEMINI_API_KEY),
        primary_model=config.GROQ_MODEL,
        fallback_model=config.GROQ_FALLBACK_MODEL,
        active_sessions_count=session_manager.get_active_count()
    )

# ==================== SESSIONS API ====================

@app.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, tags=["Sessions"])
def create_session(payload: SessionCreate):
    session = session_manager.create_session(initial_level=payload.initial_level or "coban")
    return session.to_response()

@app.get("/api/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session.to_response()

@app.patch("/api/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
def patch_session(session_id: str, payload: SessionPatch):
    session = session_manager.update_level(session_id, payload.level)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session.to_response()

# ==================== GLOSSARY EXPLAIN API ====================

@app.post("/api/explain", response_model=ExplainResponse, tags=["Glossary"])
@app.post("/api/glossary/explain", response_model=ExplainResponse, tags=["Glossary"])
def explain_term(req: ExplainRequest):
    # Lấy hoặc khởi tạo session
    session = None
    level = req.learner_level or "coban"
    
    if req.session_id:
        session = session_manager.get_session(req.session_id)
        if session:
            level = session.level
        else:
            session = session_manager.create_session(initial_level=level)

    if not req.selected_text or not req.selected_text.strip():
        raise HTTPException(status_code=400, detail="selected_text cannot be empty")

    # Gọi LLM Client với Groq primary -> Groq fallback -> Gemini fallback
    parsed_json, used_model = llm_client.explain_term(
        selected_text=req.selected_text.strip(),
        surrounding_context=req.surrounding_context or "",
        learner_level=level
    )

    # Parse list of related concepts
    related_list = []
    for rc in parsed_json.get("related_concepts", []):
        if isinstance(rc, dict) and "concept" in rc and "relationship" in rc:
            related_list.append(RelatedConcept(concept=rc["concept"], relationship=rc["relationship"]))

    # Kiểm tra xem từ đã được lưu trong session hay chưa
    is_saved = False
    saved_term_id = None
    if session:
        for t_id, st in session.saved_terms.items():
            if st.term.lower() == req.selected_text.strip().lower():
                is_saved = True
                saved_term_id = t_id
                break

    response_data = ExplainResponse(
        term=parsed_json.get("term", req.selected_text.strip()),
        expanded_form=parsed_json.get("expanded_form"),
        meaning_in_context=parsed_json.get("meaning_in_context", "Nghĩa của thuật ngữ trong ngữ cảnh."),
        plain_explanation=parsed_json.get("plain_explanation", "Giải thích ngắn gọn cho người mới."),
        example=parsed_json.get("example", "Ví dụ minh họa."),
        related_concepts=related_list,
        confidence=parsed_json.get("confidence", "high"),
        evidence_span=parsed_json.get("evidence_span"),
        clarifying_question=parsed_json.get("clarifying_question"),
        used_model=used_model,
        saved=is_saved,
        term_id=saved_term_id
    )

    # Ghi nhận lượt hỏi vào chat history của session
    if session:
        session_manager.add_chat_turn(
            session.session_id,
            "user",
            f"Bôi đen: '{req.selected_text}' | Context: '{req.surrounding_context}'"
        )
        session_manager.add_chat_turn(
            session.session_id,
            "assistant",
            f"Giải thích: {response_data.meaning_in_context} [{used_model}]"
        )

    return response_data

# ==================== SAVED TERMS (VOCABULARY) API ====================

@app.post("/api/sessions/{session_id}/saved-terms", response_model=SavedTerm, status_code=status.HTTP_201_CREATED, tags=["Vocabulary"])
def save_term(session_id: str, payload: SavedTermCreate):
    term_dict = payload.model_dump()
    saved_term = session_manager.save_term(session_id, term_dict)
    return saved_term

@app.get("/api/sessions/{session_id}/saved-terms", response_model=SavedTermListResponse, tags=["Vocabulary"])
def list_saved_terms(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    terms = session_manager.get_saved_terms(session_id)
    return SavedTermListResponse(
        session_id=session_id,
        total=len(terms),
        terms=terms
    )

@app.delete("/api/sessions/{session_id}/saved-terms/{term_id}", tags=["Vocabulary"])
def delete_saved_term(session_id: str, term_id: str):
    success = session_manager.delete_saved_term(session_id, term_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Term {term_id} in session {session_id} not found")
    return {"status": "deleted", "term_id": term_id, "session_id": session_id}

# ==================== CHAT TUTOR API ====================

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
def chat_tutor(req: ChatRequest):
    session = session_manager.get_or_create_session(req.session_id)
    
    reply, used_model = llm_client.chat_tutor(
        message=req.message,
        context=req.context,
        history=session.chat_history
    )

    session_manager.add_chat_turn(session.session_id, "user", req.message)
    session_manager.add_chat_turn(session.session_id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        used_model=used_model,
        session_id=session.session_id,
        status="ok"
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
