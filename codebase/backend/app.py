import os
import re
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

from config import config
from schemas import (
    ExplainRequest, ExplainResponse, RelatedConcept, ComparisonConcept, QuizItem, QuizOption,
    SessionCreate, SessionPatch, SessionResponse,
    SavedTerm, SavedTermCreate, SavedTermListResponse,
    QuizSubmitRequest, QuizSubmitResponse, LearningProgress,
    TermDetectionRequest, TermDetectionResponse, DetectedTerm,
    FlashcardReviewRequest,
    ChatRequest, ChatResponse, HealthResponse,
    SlideSearchRequest, SlideSearchResponse, SlideSearchResult
)
from llm_client import llm_client
from sessions import session_manager
from eval_logger import log_explain_interaction
from retriever_provider import get_retriever

app = FastAPI(
    title="VLearn AI Tutor & Glossary API",
    description="Backend AI Tutor: tự phát hiện thuật ngữ khó trong slide, giải thích theo ngữ cảnh với 4 cách học (Tóm tắt/Ví dụ/So sánh/Chuyên sâu), quiz active-recall, cập nhật learning profile, tự sinh flashcard và nhắc ôn theo spaced repetition cho VLearn",
    version="1.3.0"
)

# Từ điển thuật ngữ AI phổ biến dùng để tự nhận diện trong nội dung slide (bước "Hệ thống tự nhận diện thuật ngữ khó").
# Có thể mở rộng thêm; matching theo word-boundary, không phân biệt hoa thường.
KNOWN_AI_TERMS: Dict[str, Optional[str]] = {
    "RLHF": "Reinforcement Learning from Human Feedback",
    "SFT": "Supervised Fine-Tuning",
    "RAG": "Retrieval-Augmented Generation",
    "LoRA": "Low-Rank Adaptation",
    "CoT": "Chain-of-Thought",
    "MCP": "Model Context Protocol",
    "LLM": "Large Language Model",
    "RNN": "Recurrent Neural Network",
    "CNN": "Convolutional Neural Network",
    "GAN": "Generative Adversarial Network",
    "DPO": "Direct Preference Optimization",
    "PPO": "Proximal Policy Optimization",
    "Transformer": None,
    "Attention": None,
    "Embedding": None,
    "Token": None,
    "Temperature": None,
    "Fine-tuning": None,
    "Prompt Engineering": None,
    "Zero-shot": None,
    "Few-shot": None,
    "Context window": None,
    "Vector Database": None,
    "Agent": None,
}

# Ước lượng độ khó theo trình độ người học (heuristic đơn giản, không gọi LLM để giữ tốc độ quét slide nhanh).
# - ALWAYS_EASY: hầu hết mọi trình độ đều không thấy khó (thuật ngữ quá phổ biến).
# - ADVANCED_HARD_ONLY: chỉ còn khó với người "nangcao"; "coban"/"thongthao" thì các thuật ngữ khác cũng khó.
ALWAYS_EASY_TERMS = {"llm", "token", "agent"}
ADVANCED_HARD_ONLY_TERMS = {"mcp", "dpo", "ppo"}
# Với learner "thongthao": các thuật ngữ dưới đây coi như đã nắm được, không tính là khó
THONGTHAO_KNOWN_TERMS = {
    "rnn", "cnn", "transformer", "attention", "embedding", "fine-tuning",
    "prompt engineering", "zero-shot", "few-shot", "context window",
    "vector database", "temperature"
} | ALWAYS_EASY_TERMS

# Ngưỡng số từ trong surrounding_context: dưới ngưỡng này coi là "quá ngắn" và
# thử tự động tra cứu thêm ngữ cảnh thật từ slide index (nếu index đã được build).
MIN_CONTEXT_WORDS = 8
# Số ký tự tối đa lấy từ 1 chunk tìm được để bơm vào surrounding_context, tránh
# prompt quá dài.
MAX_RETRIEVED_CONTEXT_CHARS = 600


def _estimate_is_difficult(term_key: str, learner_level: str) -> bool:
    key = term_key.lower()
    if learner_level == "nangcao":
        return key in ADVANCED_HARD_ONLY_TERMS
    if learner_level == "thongthao":
        return key not in THONGTHAO_KNOWN_TERMS
    # "coban" (mặc định): mọi thuật ngữ chuyên ngành đều coi là khó, trừ vài từ quá phổ biến
    return key not in ALWAYS_EASY_TERMS


def _maybe_retrieve_context(selected_text: str, surrounding_context: str, document_title: Optional[str]) -> tuple[str, Optional[dict]]:
    """Nếu surrounding_context quá ngắn/rỗng, thử tra cứu lại đoạn slide thật chứa
    selected_text từ slide index (nếu đã build). Trả về (context_to_use, retrieved_meta).
    retrieved_meta = None nếu không tra cứu / không tìm thấy gì -> hành vi giữ nguyên như cũ.
    Hàm này KHÔNG bao giờ raise ra ngoài — retrieval là tính năng tăng cường (augment),
    lỗi ở đây không được phép làm hỏng luồng /api/explain chính."""
    context_word_count = len((surrounding_context or "").split())
    if context_word_count >= MIN_CONTEXT_WORDS:
        return surrounding_context, None

    try:
        retriever = get_retriever()
        if retriever is None:
            return surrounding_context, None

        document_id = document_title  # build_index.py dùng tên file làm document_id;
        # nếu frontend gửi document_title khớp document_id thật thì lọc đúng tài liệu,
        # còn không thì tìm kiếm trên toàn bộ corpus (document_id=None).
        results = retriever.search(selected_text, limit=1, document_id=document_id)
        if not results:
            results = retriever.search(selected_text, limit=1, document_id=None)
        if not results:
            return surrounding_context, None

        best = results[0]
        chunk = best.to_dict()
        retrieved_text = str(chunk["content"])[:MAX_RETRIEVED_CONTEXT_CHARS]

        # Nối vào context cũ (nếu có) thay vì ghi đè hoàn toàn, để không mất thông tin
        # người dùng đã cung cấp.
        combined = (surrounding_context.strip() + " " + retrieved_text).strip() if surrounding_context else retrieved_text

        return combined, {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "citation": chunk["citation"],
            "score": chunk["score"],
        }
    except Exception:
        # Augment thất bại -> quay về hành vi cũ, không ảnh hưởng luồng chính
        return surrounding_context, None


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


# ==================== TERM DETECTION (bước "Người học mở slide -> Hệ thống tự nhận diện thuật ngữ") ====================

@app.post("/api/terms/detect", response_model=TermDetectionResponse, tags=["Glossary"])
def detect_terms(req: TermDetectionRequest):
    """
    Khi người học mở 1 slide, quét toàn bộ text, tự động khoanh vùng các thuật ngữ AI
    đã biết và ước lượng thuật ngữ nào là "khó" đối với learner_level hiện tại, để
    frontend highlight sẵn đúng những chỗ người học nhiều khả năng cần giải thích.
    """
    text = req.slide_text or ""
    level = req.learner_level or "coban"
    found: list = []
    seen_spans = set()

    for term, expanded in KNOWN_AI_TERMS.items():
        pattern = r"\b" + re.escape(term) + r"\b"
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            span = (m.start(), m.end())
            if span in seen_spans:
                continue
            seen_spans.add(span)
            is_difficult = _estimate_is_difficult(term, level)
            if req.only_difficult and not is_difficult:
                continue
            found.append(DetectedTerm(
                term=m.group(0), start=m.start(), end=m.end(),
                expanded_form=expanded, is_difficult=is_difficult
            ))

    found.sort(key=lambda d: d.start)
    max_terms = req.max_terms or 30
    found = found[:max_terms]

    return TermDetectionResponse(
        document_title=req.document_title,
        total_detected=len(found),
        terms=found
    )


# ==================== SLIDE RETRIEVAL (tra cứu ngữ cảnh thật từ slide/transcript) ====================

@app.post("/api/slides/search", response_model=SlideSearchResponse, tags=["Retrieval"])
def search_slides(req: SlideSearchRequest):
    """
    Tra cứu trực tiếp trong slide index (BM25-like) — dùng để debug retrieval,
    hoặc để frontend tự lấy thêm ngữ cảnh trước khi gọi /api/explain.
    Trả về danh sách rỗng (không lỗi) nếu index chưa được build bằng build_index.py.
    """
    retriever = get_retriever()
    if retriever is None:
        return SlideSearchResponse(query=req.query, total=0, results=[])

    results = retriever.search(req.query, limit=req.limit or 4, document_id=req.document_id)
    return SlideSearchResponse(
        query=req.query,
        total=len(results),
        results=[SlideSearchResult(**r.to_dict()) for r in results]
    )


# ==================== GLOSSARY EXPLAIN API ====================
# Luồng: Bôi đen -> Giải thích ngữ cảnh -> AI đánh giá độ khó -> Người học chọn kiểu giải thích ->
#        Sinh ví dụ -> So sánh khái niệm đã biết -> Quiz 1 câu (bước "Lưu tiến độ học" nằm ở /api/quiz/submit)

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

    explain_style = req.explain_style or "tomtat"
    if explain_style not in ("tomtat", "vidu", "sosanh", "chuyensau"):
        explain_style = "tomtat"

    # Nếu context người dùng gửi lên quá ngắn/rỗng, thử tự động tra thêm ngữ cảnh
    # thật từ slide index (an toàn: không tìm thấy / chưa build index -> giữ nguyên
    # hành vi cũ, không ảnh hưởng gì tới flow hiện tại).
    effective_context, retrieval_meta = _maybe_retrieve_context(
        req.selected_text.strip(), req.surrounding_context or "", req.document_title
    )

    # Gọi LLM Client: Groq primary -> Groq fallback -> Gemini fallback -> rule-engine
    parsed_json, used_model = llm_client.explain_term(
        selected_text=req.selected_text.strip(),
        surrounding_context=effective_context,
        learner_level=level,
        explain_style=explain_style
    )

    # Parse related concepts
    related_list = []
    for rc in parsed_json.get("related_concepts", []):
        if isinstance(rc, dict) and "concept" in rc and "relationship" in rc:
            related_list.append(RelatedConcept(concept=rc["concept"], relationship=rc["relationship"]))

    # Parse comparison concept ("So sánh với khái niệm đã biết")
    comparison_concept = None
    cc = parsed_json.get("comparison_concept")
    if isinstance(cc, dict) and cc.get("concept") and cc.get("comparison"):
        comparison_concept = ComparisonConcept(concept=cc["concept"], comparison=cc["comparison"])

    # Parse quiz ("Quiz 1 câu")
    quiz = None
    q = parsed_json.get("quiz")
    if isinstance(q, dict) and q.get("question") and q.get("options") and q.get("correct_key"):
        try:
            options = [QuizOption(key=o["key"], text=o["text"]) for o in q["options"] if isinstance(o, dict) and "key" in o and "text" in o]
            if options and any(opt.key == q["correct_key"] for opt in options):
                quiz = QuizItem(
                    question=q["question"],
                    options=options,
                    correct_key=q["correct_key"],
                    explanation=q.get("explanation", "")
                )
        except Exception:
            quiz = None

    # Kiểm tra xem từ đã được lưu trong session hay chưa
    is_saved = False
    saved_term_id = None
    if session:
        for t_id, st in session.saved_terms.items():
            if st.term.lower() == req.selected_text.strip().lower():
                is_saved = True
                saved_term_id = t_id
                break

    # Nếu retrieval tìm được citation thật và LLM không tự trả evidence_span,
    # dùng citation đó làm evidence_span để người học biết nguồn (không ghi đè
    # nếu model đã tự trích được evidence_span từ context có sẵn).
    evidence_span = parsed_json.get("evidence_span")
    if not evidence_span and retrieval_meta:
        evidence_span = retrieval_meta["citation"]

    response_data = ExplainResponse(
        term=parsed_json.get("term", req.selected_text.strip()),
        expanded_form=parsed_json.get("expanded_form"),
        meaning_in_context=parsed_json.get("meaning_in_context", "Nghĩa của thuật ngữ trong ngữ cảnh."),
        plain_explanation=parsed_json.get("plain_explanation", "Giải thích ngắn gọn cho người mới."),
        explain_style=explain_style,
        styled_explanation=parsed_json.get("styled_explanation") or parsed_json.get("plain_explanation", ""),
        is_difficult=bool(parsed_json.get("is_difficult", False)),
        difficulty_reason=parsed_json.get("difficulty_reason"),
        example=parsed_json.get("example", "Ví dụ minh họa."),
        comparison_concept=comparison_concept,
        related_concepts=related_list,
        confidence=parsed_json.get("confidence", "high"),
        evidence_span=evidence_span,
        clarifying_question=parsed_json.get("clarifying_question"),
        quiz=quiz,
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

    # Ghi log lượt bôi đen -> giải thích THẬT này vào eval/live_interactions.jsonl
    # (không raise lỗi ra ngoài — xem eval_logger.py). Dữ liệu này dùng để sau
    # xây golden set từ chatlog thật, theo guide §1.3 / §2.6.
    log_explain_interaction(
        selected_text=req.selected_text.strip(),
        surrounding_context=req.surrounding_context or "",
        learner_level=level,
        explain_style=explain_style,
        session_id=session.session_id if session else req.session_id,
        document_title=req.document_title,
        url=req.url,
        used_model=used_model,
        response_data={**response_data.model_dump(), "retrieval_meta": retrieval_meta},
    )

    return response_data


# ==================== QUIZ SUBMIT (Active Recall: chấm điểm -> cập nhật Learning Profile -> tự sinh Flashcard) ====================

@app.post("/api/quiz/submit", response_model=QuizSubmitResponse, tags=["Quiz"])
def submit_quiz(req: QuizSubmitRequest):
    """
    Luồng: AI sinh câu hỏi (ở /api/explain) -> Người học trả lời -> endpoint này chấm điểm
    (stateless, không cần backend nhớ quiz trước đó) -> cập nhật Learning Profile (số câu
    đúng/sai, streak) -> tự động tạo Flashcard cho thuật ngữ này nếu chưa có (term_data) ->
    lịch "nhắc ôn lại" của flashcard được khởi tạo/cập nhật ngay theo kết quả quiz.
    """
    session = session_manager.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")

    valid_keys = {opt.key for opt in req.quiz.options}
    if req.selected_key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"selected_key '{req.selected_key}' không nằm trong danh sách đáp án hợp lệ")

    is_correct = req.selected_key == req.quiz.correct_key

    term_id = req.term_id
    # Tự sinh flashcard nếu chưa có sẵn (term_id) nhưng client gửi kèm đủ dữ liệu thuật ngữ
    if not term_id and req.term_data:
        term_dict = req.term_data.model_dump()
        # Luôn đính kèm chính câu quiz vừa làm vào flashcard mới tạo, kể cả khi
        # client không tự gửi field "quiz" trong term_data — để thẻ này có sẵn
        # quiz cho lần ôn tập sau (mục "Cần ôn hôm nay").
        term_dict["quiz"] = req.quiz.model_dump()
        new_card = session_manager.save_term(req.session_id, term_dict)
        if new_card:
            term_id = new_card.term_id

    # Cập nhật Learning Profile; nếu có flashcard liên quan thì lịch ôn tập (SRS) cũng được cập nhật theo
    session_manager.record_quiz_result(req.session_id, is_correct, term_id=term_id)

    progress = session_manager.get_progress(req.session_id)
    flashcard = None
    if term_id:
        refreshed_session = session_manager.get_session(req.session_id)
        flashcard = refreshed_session.saved_terms.get(term_id) if refreshed_session else None

    return QuizSubmitResponse(
        correct=is_correct,
        correct_key=req.quiz.correct_key,
        explanation=req.quiz.explanation,
        session_id=req.session_id,
        progress=progress,
        flashcard=flashcard
    )


# ==================== LƯU TIẾN ĐỘ HỌC (progress) ====================

@app.get("/api/sessions/{session_id}/progress", response_model=LearningProgress, tags=["Progress"])
def get_progress(session_id: str):
    progress = session_manager.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return progress


# ==================== FLASHCARD: Personalized Glossary + Spaced Repetition ====================

@app.get("/api/sessions/{session_id}/flashcards/due", response_model=SavedTermListResponse, tags=["Flashcards"])
def get_due_flashcards(session_id: str):
    """Trả về các flashcard đã tới hạn cần nhắc ôn lại (bước 'Nhắc ôn bằng Spaced Repetition')."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    due_terms = session_manager.get_due_flashcards(session_id)
    return SavedTermListResponse(session_id=session_id, total=len(due_terms), terms=due_terms)


@app.post("/api/sessions/{session_id}/flashcards/{term_id}/review", response_model=SavedTerm, tags=["Flashcards"])
def review_flashcard(session_id: str, term_id: str, payload: FlashcardReviewRequest):
    """Học viên tự chấm mức độ nhớ khi ôn 1 flashcard ngoài luồng quiz; cập nhật lịch SM-2."""
    card = session_manager.review_flashcard(session_id, term_id, payload.quality)
    if not card:
        raise HTTPException(status_code=404, detail=f"Flashcard {term_id} in session {session_id} not found")
    return card


# ==================== SAVED TERMS (VOCABULARY) API ====================

@app.post("/api/sessions/{session_id}/saved-terms", response_model=SavedTerm, status_code=status.HTTP_201_CREATED, tags=["Vocabulary"])
def save_term(session_id: str, payload: SavedTermCreate):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
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
