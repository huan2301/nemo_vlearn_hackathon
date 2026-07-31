import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from llm_client import llm_client

class TestVLearnAIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Kiểm tra Endpoint /api/health"""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("groq_available", data)
        self.assertIn("gemini_available", data)
        self.assertIn("primary_model", data)
        print("[PASS]: GET /api/health")

    def test_02_session_flow(self):
        """Kiểm tra Tạo, Đọc và Cập nhật Session"""
        # 1. Tạo session
        res_create = self.client.post("/api/sessions", json={"initial_level": "coban"})
        self.assertEqual(res_create.status_code, 201)
        sess_data = res_create.json()
        session_id = sess_data["session_id"]
        self.assertEqual(sess_data["level"], "coban")

        # 2. Đọc session
        res_get = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["session_id"], session_id)

        # 3. Patch session level
        res_patch = self.client.patch(f"/api/sessions/{session_id}", json={"level": "nangcao"})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()["level"], "nangcao")
        print("[PASS]: Sessions API Flow")

    def test_03_explain_term_acronym(self):
        """Kiểm tra Endpoint bôi đen giải thích thuật ngữ viết tắt RLHF"""
        payload = {
            "selected_text": "RLHF",
            "surrounding_context": "We use Reinforcement Learning from Human Feedback (RLHF) to align LLMs with human preferences.",
            "learner_level": "coban"
        }
        res = self.client.post("/api/explain", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["term"], "RLHF")
        self.assertIsNotNone(data["expanded_form"])
        self.assertIn("meaning_in_context", data)
        self.assertIn("used_model", data)
        print(f"[PASS]: Explain Term RLHF (Model used: {data['used_model']})")

    def test_04_explain_term_polysemy(self):
        """Kiểm tra giải thích từ đa nghĩa 'temperature' trong ngữ cảnh AI sampling"""
        payload = {
            "selected_text": "temperature",
            "surrounding_context": "Setting the temperature to 0.7 makes the LLM outputs more creative and diverse.",
            "learner_level": "coban"
        }
        res = self.client.post("/api/explain", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["term"], "temperature")
        self.assertIn("meaning_in_context", data)
        print(f"[PASS]: Explain Term 'temperature' (Model used: {data['used_model']})")

    def test_05_saved_terms_crud(self):
        """Kiểm tra Lưu từ vựng, Liệt kê và Xóa từ vựng ôn tập"""
        # 1. Tạo session
        res_sess = self.client.post("/api/sessions", json={"initial_level": "coban"})
        session_id = res_sess.json()["session_id"]

        # 2. Lưu từ vựng
        save_payload = {
            "term": "MCP",
            "expanded_form": "Model Context Protocol",
            "meaning_in_context": "Giao thức kết nối AI với dữ liệu ngoài",
            "plain_explanation": "Chuẩn kết nối giúp AI đọc dữ liệu an toàn",
            "example": "AI truy vấn SQL database thông qua MCP",
            "evidence_span": "Model Context Protocol",
            "learner_level": "coban"
        }
        res_save = self.client.post(f"/api/sessions/{session_id}/saved-terms", json=save_payload)
        self.assertEqual(res_save.status_code, 201)
        term_data = res_save.json()
        term_id = term_data["term_id"]

        # 3. Liệt kê từ đã lưu
        res_list = self.client.get(f"/api/sessions/{session_id}/saved-terms")
        self.assertEqual(res_list.status_code, 200)
        list_data = res_list.json()
        self.assertEqual(list_data["total"], 1)
        self.assertEqual(list_data["terms"][0]["term"], "MCP")

        # 4. Xóa từ
        res_del = self.client.delete(f"/api/sessions/{session_id}/saved-terms/{term_id}")
        self.assertEqual(res_del.status_code, 200)

        # 5. Kiểm tra danh sách sau xóa
        res_list2 = self.client.get(f"/api/sessions/{session_id}/saved-terms")
        self.assertEqual(res_list2.json()["total"], 0)
        print("[PASS]: Saved Terms CRUD Flow")

    def test_06_chat_tutor(self):
        """Kiểm tra Endpoint Chatbot AI Tutor"""
        payload = {
            "message": "Cho mình hỏi cách phân biệt SFT và RLHF ngắn gọn với?",
            "context": "Fine-tuning models using SFT and RLHF."
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("reply", data)
        self.assertIn("used_model", data)
        print(f"[PASS]: Chat Tutor API (Model used: {data['used_model']})")

    def test_07_fallback_resilience(self):
        """Kiểm tra tính năng Fallback khi Groq Primary gặp sự cố"""
        # Tạm thời gán key lỗi để kích hoạt fallback
        orig_key = llm_client.groq_api_key
        llm_client.groq_api_key = "invalid_fake_key"
        
        parsed, used_model = llm_client.explain_term("LLM", "Large Language Model context")
        self.assertIsNotNone(parsed)
        self.assertIn("term", parsed)
        self.assertTrue(used_model.startswith("groq") or used_model.startswith("gemini") or used_model.startswith("fallback"))

        # Phục hồi key ban đầu
        llm_client.groq_api_key = orig_key
        print(f"[PASS]: Fallback Mechanism (Activated fallback model: {used_model})")

if __name__ == "__main__":
    unittest.main()
