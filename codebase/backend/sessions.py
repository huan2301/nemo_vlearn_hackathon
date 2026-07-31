import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from schemas import SessionResponse, SavedTerm, LearningProgress

class Session:
    def __init__(self, session_id: str, level: str = "coban"):
        now_str = datetime.now().isoformat()
        self.session_id: str = session_id
        self.level: str = level # coban, thongthao, nangcao
        self.created_at: str = now_str
        self.updated_at: str = now_str
        self.saved_terms: Dict[str, SavedTerm] = {}
        self.chat_history: List[Dict[str, str]] = []

        # --- Learning Progress: theo dõi kết quả quiz để tính accuracy + streak ---
        self.quiz_attempted_count: int = 0
        self.quiz_correct_count: int = 0
        self.current_streak: int = 0

    def update_level(self, new_level: str):
        self.level = new_level
        self.updated_at = datetime.now().isoformat()

    def to_response(self) -> SessionResponse:
        return SessionResponse(
            session_id=self.session_id,
            level=self.level,
            created_at=self.created_at,
            updated_at=self.updated_at,
            saved_terms_count=len(self.saved_terms),
            chat_turns_count=len(self.chat_history),
            quiz_attempted_count=self.quiz_attempted_count,
            quiz_correct_count=self.quiz_correct_count,
        )


# ==================== Spaced Repetition (SM-2 rút gọn) ====================
# quality: "again" (quên) | "hard" (khó nhớ) | "good" (nhớ được) | "easy" (nhớ dễ dàng)
# Ánh xạ sang thang điểm SM-2 gốc (0-5) để tính ease_factor/interval theo đúng công thức chuẩn.
_QUALITY_TO_SM2_SCORE: Dict[str, int] = {
    "again": 0,
    "hard": 3,
    "good": 4,
    "easy": 5,
}


def _apply_srs_review(saved_term: SavedTerm, quality: str) -> None:
    """Cập nhật lịch ôn tập (repetitions/ease_factor/interval_days/next_review_at) của 1
    flashcard theo thuật toán SM-2 rút gọn, dựa trên mức độ nhớ người học tự đánh giá
    (hoặc suy ra từ kết quả quiz đúng/sai — xem record_quiz_result)."""
    score = _QUALITY_TO_SM2_SCORE.get(quality, 3)

    if score < 3:
        # Quên bài -> học lại từ đầu, nhắc ôn lại sớm (ngay hôm sau) thay vì đợi lâu.
        saved_term.repetitions = 0
        saved_term.interval_days = 1
    else:
        if saved_term.repetitions == 0:
            saved_term.interval_days = 1
        elif saved_term.repetitions == 1:
            saved_term.interval_days = 6
        else:
            saved_term.interval_days = max(1, round(saved_term.interval_days * saved_term.ease_factor))
        saved_term.repetitions += 1

    # Công thức cập nhật ease_factor chuẩn của SM-2.
    new_ease = saved_term.ease_factor + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
    saved_term.ease_factor = max(1.3, round(new_ease, 2))

    now = datetime.now()
    saved_term.last_reviewed_at = now.isoformat()
    saved_term.next_review_at = (now + timedelta(days=saved_term.interval_days)).isoformat()


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def create_session(self, initial_level: str = "coban") -> Session:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        if initial_level not in ["coban", "thongthao", "nangcao"]:
            initial_level = "coban"
        session = Session(session_id, level=initial_level)
        self._sessions[session_id] = session
        return session

    def get_or_create_session(self, session_id: Optional[str] = None, default_level: str = "coban") -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session(initial_level=default_level)

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def update_level(self, session_id: str, level: str) -> Optional[Session]:
        session = self.get_session(session_id)
        if not session:
            return None
        if level in ["coban", "thongthao", "nangcao"]:
            session.update_level(level)
        return session

    def save_term(self, session_id: str, term_data: Dict[str, Any]) -> SavedTerm:
        session = self.get_or_create_session(session_id)
        term_id = f"term_{uuid.uuid4().hex[:8]}"
        now_str = datetime.now().isoformat()

        saved_term = SavedTerm(
            term_id=term_id,
            session_id=session.session_id,
            term=term_data.get("term", ""),
            expanded_form=term_data.get("expanded_form"),
            meaning_in_context=term_data.get("meaning_in_context", ""),
            plain_explanation=term_data.get("plain_explanation", ""),
            example=term_data.get("example", ""),
            evidence_span=term_data.get("evidence_span"),
            learner_level=term_data.get("learner_level", session.level),
            is_difficult=term_data.get("is_difficult", False),
            # Nếu term_data có kèm quiz (dict do LLM/explain sinh ra, hoặc đã được
            # gắn thêm ở app.py khi tự tạo flashcard từ /api/quiz/submit) thì lưu lại
            # luôn cùng flashcard, để hiển thị lại đúng câu hỏi này khi ôn tập sau.
            quiz=term_data.get("quiz"),
            created_at=now_str,
            # Flashcard mới -> coi như "đến hạn ôn ngay" cho tới lần ôn đầu tiên.
            next_review_at=now_str,
        )

        session.saved_terms[term_id] = saved_term
        session.updated_at = now_str
        return saved_term

    def get_saved_terms(self, session_id: str) -> List[SavedTerm]:
        session = self.get_session(session_id)
        if not session:
            return []
        return list(session.saved_terms.values())

    def delete_saved_term(self, session_id: str, term_id: str) -> bool:
        session = self.get_session(session_id)
        if not session or term_id not in session.saved_terms:
            return False
        del session.saved_terms[term_id]
        session.updated_at = datetime.now().isoformat()
        return True

    def add_chat_turn(self, session_id: str, role: str, content: str):
        session = self.get_or_create_session(session_id)
        session.chat_history.append({"role": role, "content": content})
        session.updated_at = datetime.now().isoformat()

    def get_active_count(self) -> int:
        return len(self._sessions)

    # ==================== Learning Progress ====================

    def get_progress(self, session_id: str) -> Optional[LearningProgress]:
        session = self.get_session(session_id)
        if not session:
            return None
        accuracy = (
            session.quiz_correct_count / session.quiz_attempted_count
            if session.quiz_attempted_count else 0.0
        )
        return LearningProgress(
            session_id=session.session_id,
            level=session.level,
            saved_terms_count=len(session.saved_terms),
            quiz_attempted_count=session.quiz_attempted_count,
            quiz_correct_count=session.quiz_correct_count,
            accuracy=round(accuracy, 4),
            current_streak=session.current_streak,
            updated_at=session.updated_at,
        )

    def record_quiz_result(self, session_id: str, is_correct: bool, term_id: Optional[str] = None) -> Optional[Session]:
        """Cập nhật Learning Profile (số câu đúng/sai, streak) sau 1 lượt quiz, và nếu có
        flashcard liên quan (term_id) thì cũng cập nhật lịch ôn tập SRS của flashcard đó
        theo đúng kết quả (đúng ~ 'good', sai ~ 'again')."""
        session = self.get_session(session_id)
        if not session:
            return None

        session.quiz_attempted_count += 1
        if is_correct:
            session.quiz_correct_count += 1
            session.current_streak += 1
        else:
            session.current_streak = 0
        session.updated_at = datetime.now().isoformat()

        if term_id and term_id in session.saved_terms:
            saved_term = session.saved_terms[term_id]
            _apply_srs_review(saved_term, "good" if is_correct else "again")

        return session

    # ==================== Flashcards: nhắc ôn lại theo spaced repetition ====================

    def get_due_flashcards(self, session_id: str) -> List[SavedTerm]:
        session = self.get_session(session_id)
        if not session:
            return []
        now_str = datetime.now().isoformat()
        due = [
            t for t in session.saved_terms.values()
            if not t.next_review_at or t.next_review_at <= now_str
        ]
        # Thẻ chưa từng ôn (next_review_at ban đầu = created_at) hoặc quá hạn lâu nhất lên trước.
        due.sort(key=lambda t: t.next_review_at or "")
        return due

    def review_flashcard(self, session_id: str, term_id: str, quality: str) -> Optional[SavedTerm]:
        session = self.get_session(session_id)
        if not session or term_id not in session.saved_terms:
            return None
        saved_term = session.saved_terms[term_id]
        _apply_srs_review(saved_term, quality)
        session.updated_at = datetime.now().isoformat()
        return saved_term

session_manager = SessionManager()
