import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from schemas import SessionResponse, SavedTerm

class Session:
    def __init__(self, session_id: str, level: str = "coban"):
        now_str = datetime.now().isoformat()
        self.session_id: str = session_id
        self.level: str = level # coban, thongthao, nangcao
        self.created_at: str = now_str
        self.updated_at: str = now_str
        self.saved_terms: Dict[str, SavedTerm] = {}
        self.chat_history: List[Dict[str, str]] = []

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
            chat_turns_count=len(self.chat_history)
        )

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
            created_at=now_str
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

session_manager = SessionManager()
