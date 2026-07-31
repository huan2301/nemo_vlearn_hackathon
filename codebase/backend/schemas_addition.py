# ==================== THÊM VÀO CUỐI schemas.py — cho SlideRetriever ====================

class SlideSearchRequest(BaseModel):
    query: str = Field(..., description="Từ khóa/thuật ngữ cần tra trong slide index")
    document_id: Optional[str] = Field(None, description="Lọc theo 1 tài liệu cụ thể (khớp document_id trong slide_index.jsonl); để trống để tìm trên toàn bộ corpus")
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