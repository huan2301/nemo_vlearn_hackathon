from typing import List, Optional
from pydantic import BaseModel, Field

class RelatedConcept(BaseModel):
    concept: str = Field(..., description="Tên khái niệm liên quan")
    relationship: str = Field(..., description="Mối quan hệ ngắn gọn với thuật ngữ chính")

class ExplainRequest(BaseModel):
    selected_text: str = Field(..., description="Thuật ngữ hoặc cụm từ được bôi đen (1-6 từ)")
    surrounding_context: Optional[str] = Field("", description="1-2 câu xung quanh đoạn bôi đen làm ngữ cảnh")
    learner_level: Optional[str] = Field("coban", description="Trình độ người học: coban, thongthao, nangcao")
    session_id: Optional[str] = Field(None, description="ID phiên làm việc hiện tại")
    document_title: Optional[str] = Field(None, description="Tiêu đề tài liệu/trang web")
    url: Optional[str] = Field(None, description="URL trang tài liệu")

class ExplainResponse(BaseModel):
    term: str = Field(..., description="Đúng cụm từ người dùng bôi đen")
    expanded_form: Optional[str] = Field(None, description="Tên đầy đủ nếu là từ viết tắt (VD: RLHF -> Reinforcement Learning from Human Feedback)")
    meaning_in_context: str = Field(..., description="1 câu giải thích nghĩa đang được dùng trong đoạn văn")
    plain_explanation: str = Field(..., description="Lời giải thích dễ hiểu cho người mới (dưới 80 từ)")
    example: str = Field(..., description="Ví dụ minh họa thực tế dễ hình dung (dưới 50 từ)")
    related_concepts: List[RelatedConcept] = Field(default_factory=list, description="Tối đa 3 khái niệm liên quan")
    confidence: str = Field(..., description="Mức độ tin cậy căn cứ: high | low | insufficient")
    evidence_span: Optional[str] = Field(None, description="Trích đoạn ngắn (max 25 từ) từ ngữ cảnh làm bằng chứng")
    clarifying_question: Optional[str] = Field(None, description="Câu hỏi làm rõ nếu confidence = insufficient")
    used_model: str = Field(..., description="Tên AI Provider & Model thực tế đã trả lời")
    saved: bool = Field(False, description="Thuật ngữ đã được lưu vào danh sách ôn tập hay chưa")
    term_id: Optional[str] = Field(None, description="ID của thuật ngữ đã lưu")

class SessionCreate(BaseModel):
    initial_level: Optional[str] = Field("coban", description="Trình độ khởi tạo: coban, thongthao, nangcao")

class SessionPatch(BaseModel):
    level: str = Field(..., description="Cập nhật trình độ mới: coban, thongthao, nangcao")

class SessionResponse(BaseModel):
    session_id: str
    level: str
    created_at: str
    updated_at: str
    saved_terms_count: int = 0
    chat_turns_count: int = 0

class SavedTerm(BaseModel):
    term_id: str
    session_id: str
    term: str
    expanded_form: Optional[str] = None
    meaning_in_context: str
    plain_explanation: str
    example: str
    evidence_span: Optional[str] = None
    learner_level: str
    created_at: str

class SavedTermCreate(BaseModel):
    term: str
    expanded_form: Optional[str] = None
    meaning_in_context: str
    plain_explanation: str
    example: str
    evidence_span: Optional[str] = None
    learner_level: Optional[str] = "coban"

class SavedTermListResponse(BaseModel):
    session_id: str
    total: int
    terms: List[SavedTerm]

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="ID phiên học")
    message: str = Field(..., description="Câu hỏi hoặc thắc mắc của học viên")
    selected_text: Optional[str] = Field(None, description="Thuật ngữ bôi đen (nếu có)")
    context: Optional[str] = Field(None, description="Ngữ cảnh văn bản (nếu có)")

class ChatResponse(BaseModel):
    reply: str
    used_model: str
    session_id: str
    status: str = "ok" # ok, insufficient_source, error

class HealthResponse(BaseModel):
    status: str
    groq_available: bool
    gemini_available: bool
    primary_model: str
    fallback_model: str
    active_sessions_count: int
