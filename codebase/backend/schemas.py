from typing import List, Optional
from pydantic import BaseModel, Field


class RelatedConcept(BaseModel):
    concept: str = Field(..., description="Tên khái niệm liên quan")
    relationship: str = Field(..., description="Mối quan hệ ngắn gọn với thuật ngữ chính")


# ==================== So sánh với khái niệm đã biết ====================

class ComparisonConcept(BaseModel):
    concept: str = Field(..., description="Khái niệm quen thuộc mà người học nhiều khả năng đã biết")
    comparison: str = Field(..., description="Câu so sánh ngắn gọn giữa thuật ngữ mới và khái niệm đã biết")


# ==================== Quiz 1 câu ====================

class QuizOption(BaseModel):
    key: str = Field(..., description="Ký hiệu đáp án, VD: A, B, C, D")
    text: str = Field(..., description="Nội dung đáp án")


class QuizItem(BaseModel):
    question: str = Field(..., description="Câu hỏi trắc nghiệm kiểm tra hiểu bài (1 câu)")
    options: List[QuizOption] = Field(..., description="Danh sách đáp án (thường 4 lựa chọn)")
    correct_key: str = Field(..., description="Key của đáp án đúng, VD: A")
    explanation: str = Field(..., description="Giải thích ngắn tại sao đáp án đó đúng")


# ==================== Hệ thống tự nhận diện thuật ngữ KHÓ (bước "mở slide") ====================

class DetectedTerm(BaseModel):
    term: str = Field(..., description="Thuật ngữ AI được phát hiện trong slide")
    start: int = Field(..., description="Vị trí ký tự bắt đầu trong slide_text")
    end: int = Field(..., description="Vị trí ký tự kết thúc (không bao gồm) trong slide_text")
    expanded_form: Optional[str] = Field(None, description="Tên đầy đủ nếu là từ viết tắt đã biết")
    is_difficult: bool = Field(True, description="Ước lượng thuật ngữ này có khó với learner_level hiện tại hay không")


class TermDetectionRequest(BaseModel):
    slide_text: str = Field(..., description="Toàn bộ nội dung text của slide/trang đang mở")
    document_title: Optional[str] = Field(None, description="Tiêu đề tài liệu/slide")
    learner_level: Optional[str] = Field("coban", description="Trình độ người học hiện tại, dùng để ước lượng thuật ngữ nào là 'khó'")
    max_terms: Optional[int] = Field(30, description="Số lượng thuật ngữ tối đa trả về")
    only_difficult: Optional[bool] = Field(False, description="Nếu true, chỉ trả về các thuật ngữ được đánh giá là khó")


class TermDetectionResponse(BaseModel):
    document_title: Optional[str] = None
    total_detected: int
    terms: List[DetectedTerm]


# 4 cách học người học có thể chọn sau khi xem giải thích ngữ cảnh: Tóm tắt / Ví dụ / So sánh / Chuyên sâu
EXPLAIN_STYLES = ("tomtat", "vidu", "sosanh", "chuyensau")


class ExplainRequest(BaseModel):
    selected_text: str = Field(..., description="Thuật ngữ hoặc cụm từ được bôi đen/bấm chọn (1-6 từ)")
    surrounding_context: Optional[str] = Field("", description="1-2 câu xung quanh đoạn bôi đen làm ngữ cảnh")
    learner_level: Optional[str] = Field("coban", description="Trình độ người học: coban, thongthao, nangcao")
    explain_style: Optional[str] = Field(
        "tomtat",
        description="Cách học người học chọn: 'tomtat' (Tóm tắt), 'vidu' (Ví dụ), 'sosanh' (So sánh), 'chuyensau' (Chuyên sâu)"
    )
    session_id: Optional[str] = Field(None, description="ID phiên làm việc hiện tại")
    document_title: Optional[str] = Field(None, description="Tiêu đề tài liệu/trang web")
    url: Optional[str] = Field(None, description="URL trang tài liệu")




class ExplainResponse(BaseModel):
    term: str = Field(..., description="Đúng cụm từ người dùng bôi đen")
    expanded_form: Optional[str] = Field(None, description="Tên đầy đủ nếu là từ viết tắt (VD: RLHF -> Reinforcement Learning from Human Feedback)")
    meaning_in_context: str = Field(..., description="1 câu giải thích nghĩa đang được dùng trong đoạn văn")
    plain_explanation: str = Field(..., description="Lời giải thích dễ hiểu cho người mới (dưới 80 từ)")

    # --- Người học chọn cách học: Tóm tắt / Ví dụ / So sánh / Chuyên sâu ---
    explain_style: str = Field(default="tomtat", description="Cách học đã áp dụng: tomtat | vidu | sosanh | chuyensau")
    styled_explanation: str = Field(default="", description="Nội dung giải thích đã được điều chỉnh theo explain_style")

    # --- AI đánh giá "Từ này có vẻ khó" ---
    is_difficult: bool = Field(False, description="AI đánh giá thuật ngữ này có khó với learner_level hay không")
    difficulty_reason: Optional[str] = Field(None, description="Lý do ngắn gọn vì sao thuật ngữ được đánh giá là khó")

    # --- Sinh ví dụ ---
    example: str = Field(..., description="Ví dụ minh họa thực tế dễ hình dung (dưới 50 từ)")

    # --- So sánh với khái niệm đã biết ---
    comparison_concept: Optional[ComparisonConcept] = Field(None, description="So sánh thuật ngữ mới với khái niệm quen thuộc đã biết")

    related_concepts: List[RelatedConcept] = Field(default_factory=list, description="Tối đa 3 khái niệm liên quan")
    confidence: str = Field(..., description="Mức độ tin cậy căn cứ: high | low | insufficient")
    evidence_span: Optional[str] = Field(None, description="Trích đoạn ngắn (max 25 từ) từ ngữ cảnh làm bằng chứng")
    clarifying_question: Optional[str] = Field(None, description="Câu hỏi làm rõ nếu confidence = insufficient")

    # --- Quiz 1 câu ---
    quiz: Optional[QuizItem] = Field(None, description="1 câu hỏi trắc nghiệm để kiểm tra người học vừa hiểu bài chưa")

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
    quiz_attempted_count: int = 0
    quiz_correct_count: int = 0


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
    is_difficult: bool = False
    created_at: str

    # --- Flashcard + nhắc ôn lại (spaced repetition, thuật toán SM-2 rút gọn) ---
    repetitions: int = Field(0, description="Số lần đã ôn thành công liên tiếp")
    ease_factor: float = Field(2.5, description="Hệ số dễ nhớ, càng cao thì khoảng ôn tăng càng nhanh")
    interval_days: int = Field(0, description="Khoảng cách (ngày) đến lần ôn tiếp theo")
    last_reviewed_at: Optional[str] = Field(None, description="Thời điểm ôn tập gần nhất")
    next_review_at: Optional[str] = Field(None, description="Thời điểm hệ thống sẽ nhắc ôn lại tiếp theo")


class SavedTermCreate(BaseModel):
    term: str
    expanded_form: Optional[str] = None
    meaning_in_context: str
    plain_explanation: str
    example: str
    evidence_span: Optional[str] = None
    learner_level: Optional[str] = "coban"
    is_difficult: Optional[bool] = False


class SavedTermListResponse(BaseModel):
    session_id: str
    total: int
    terms: List[SavedTerm]


# ==================== Lưu tiến độ học ====================

class QuizSubmitRequest(BaseModel):
    session_id: str = Field(..., description="ID phiên học")
    term: str = Field(..., description="Thuật ngữ đang được kiểm tra")
    term_id: Optional[str] = Field(None, description="ID flashcard đã tồn tại (nếu có) — nếu truyền vào, kết quả quiz sẽ cập nhật lịch ôn tập của flashcard này")
    term_data: Optional[SavedTermCreate] = Field(
        None,
        description="Dữ liệu đầy đủ của thuật ngữ (lấy từ response của /api/explain). Nếu term_id không có mà term_data có, "
                    "hệ thống sẽ TỰ ĐỘNG SINH 1 FLASHCARD MỚI ngay sau khi chấm điểm quiz."
    )
    quiz: QuizItem = Field(..., description="Đối tượng quiz mà client nhận được từ /api/explain, gửi lại để server chấm điểm")
    selected_key: str = Field(..., description="Đáp án học viên chọn, VD: A")


# ==================== Flashcard: nhắc ôn lại theo spaced repetition ====================

class FlashcardReviewRequest(BaseModel):
    quality: str = Field(
        ...,
        description="Học viên tự đánh giá mức độ nhớ: 'again' (quên), 'hard' (khó nhớ), 'good' (nhớ được), 'easy' (nhớ dễ dàng)"
    )


class LearningProgress(BaseModel):
    session_id: str
    level: str
    saved_terms_count: int
    quiz_attempted_count: int
    quiz_correct_count: int
    accuracy: float = Field(..., description="Tỷ lệ trả lời đúng quiz (0.0 - 1.0)")
    current_streak: int = Field(..., description="Số câu quiz đúng liên tiếp gần nhất")
    updated_at: str


class QuizSubmitResponse(BaseModel):
    correct: bool
    correct_key: str
    explanation: str
    session_id: str
    progress: LearningProgress
    flashcard: Optional[SavedTerm] = Field(
        None,
        description="Flashcard đã được cập nhật lịch ôn tập nếu request có kèm term_id hợp lệ"
    )


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="ID phiên học")
    message: str = Field(..., description="Câu hỏi hoặc thắc mắc của học viên")
    selected_text: Optional[str] = Field(None, description="Thuật ngữ bôi đen (nếu có)")
    context: Optional[str] = Field(None, description="Ngữ cảnh văn bản (nếu có)")


class ChatResponse(BaseModel):
    reply: str
    used_model: str
    session_id: str
    status: str = "ok"  # ok, insufficient_source, error


class SlideSearchRequest(BaseModel):
    query: str = Field(..., description="Từ khóa/thuật ngữ cần tra trong slide index")
    document_id: Optional[str] = Field(None, description="Lọc theo 1 tài liệu cụ thể")
    limit: Optional[int] = Field(4, description="Số chunk tối đa trả về")


class SlideSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    page: int
    page_title: str
    citation: str
    content: str
    score: float


class SlideSearchResponse(BaseModel):
    query: str
    total: int
    results: List[SlideSearchResult]


class HealthResponse(BaseModel):
    status: str
    groq_available: bool
    gemini_available: bool
    primary_model: str
    fallback_model: str
    active_sessions_count: int