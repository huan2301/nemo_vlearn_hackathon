# Deploy miễn phí — AI Glossary Tutor

Backend (FastAPI) → **Render** (free Web Service). Frontend (static HTML/CSS/JS) → **Cloudflare Pages**.
Cả hai đều $0, không cần thẻ tín dụng, key API không bao giờ nằm trong code/git — chỉ set qua ô "Environment Variables/Secrets" của từng dịch vụ.

## 1. Deploy backend lên Render

1. Push code lên GitHub (repo hiện tại: `github.com/huan2301/nemo_vlearn_hackathon`) — đảm bảo đã push nhánh bạn muốn deploy.
2. Vào [render.com](https://render.com) → tạo tài khoản (free, không cần thẻ) → **New → Blueprint** → chọn repo này. Render sẽ tự đọc file `render.yaml` ở gốc repo và cấu hình sẵn build/start command.
3. Khi được hỏi giá trị cho các biến môi trường, điền:
   - `GROQ_API_KEY` — key Groq thật của bạn
   - `GROQ_FALLBACK_API_KEY` — có thể để trống, code sẽ tự dùng lại `GROQ_API_KEY`
   - `GEMINI_API_KEY` — key Gemini thật của bạn (nếu có dùng)
   - Nếu bỏ lỡ bước này, vào service vừa tạo → tab **Environment** → thêm sau cũng được.
4. Bấm Apply, đợi build xong (~2-3 phút). Copy URL Render cấp cho bạn, dạng `https://vlearn-ai-tutor-backend.onrender.com`.

**Lưu ý free tier của Render:** sau 15 phút không có ai gọi, service tự ngủ; request đầu tiên sau đó mất ~30-60s để "thức dậy". Session lưu trong RAM cũng mất khi service ngủ/deploy lại — nhưng phần "Sổ tay ôn tập" ở frontend đã có cache localStorage + tự resync nên người học vẫn thấy lại từ đã lưu, không bị mất trắng.

## 2. Trỏ frontend về backend thật

Mở `codebase/frontend/js/config.js`, sửa dòng:
```js
const PROD_API_BASE = "https://REPLACE_WITH_YOUR_BACKEND_URL.onrender.com";
```
thành đúng URL Render vừa cấp ở bước 1, rồi commit + push. (Chạy local ở `127.0.0.1`/`localhost` thì file này tự động bỏ qua, vẫn dùng backend local như cũ — không cần sửa gì khi phát triển tiếp trên máy.)

## 3. Deploy frontend lên Cloudflare Pages

> Làm bước này SAU KHI đã xong Bước 1 (deploy Render) và Bước 2 (điền URL Render thật vào `config.js` rồi push) — nếu chưa, trang deploy xong sẽ không gọi được AI vì vẫn đang trỏ về URL placeholder.

1. Vào **[pages.cloudflare.com](https://pages.cloudflare.com)** → đăng nhập/tạo tài khoản Cloudflare (miễn phí, không cần thẻ).
2. Ở sidebar bên trái, chọn **Workers & Pages** → bấm **Create application**.
3. Chọn tab **Pages** (không phải Workers) → bấm **Connect to Git**.
4. Cấp quyền cho Cloudflare truy cập GitHub (nếu lần đầu) → chọn repo **`nemo_vlearn_hackathon`** → chọn đúng **nhánh (branch)** bạn muốn deploy (VD `dthoai_01770` hoặc `main`) → **Begin setup**.
5. Ở màn "Set up builds and deployments", điền đúng:
   - **Project name**: tuỳ bạn đặt (sẽ thành `https://<tên-này>.pages.dev`)
   - **Production branch**: nhánh đã chọn ở bước 4
   - **Framework preset**: chọn **None**
   - **Build command**: để **trống** (không cần build, đây là HTML/CSS/JS thuần)
   - **Build output directory**: gõ `codebase/frontend`
6. Bấm **Save and Deploy**. Đợi ~30-60 giây, Cloudflare cấp 1 URL dạng `https://<tên-project>.pages.dev` — đây chính là link demo cuối cùng, gửi cho giám khảo/bạn học thử được luôn.
7. Từ giờ về sau, mỗi lần bạn `git push` lên nhánh production đó, Cloudflare **tự động deploy lại** — không cần bấm gì thêm.

**Kiểm tra nhanh sau khi deploy:** mở link `.pages.dev` → bôi đen 1 từ trên slide → nếu ra kết quả giải thích thật (không phải lỗi "Không gọi được AI") nghĩa là frontend đã trỏ đúng về backend Render.

## Việc mình đã chuẩn bị sẵn trong code

- `codebase/frontend/js/config.js` (mới): nơi DUY NHẤT cần sửa 1 dòng sau khi có URL backend — `app.js` không còn hard-code `127.0.0.1:8000` nữa, tự nhận diện local vs. production.
- `render.yaml` (mới, ở gốc repo): Render đọc file này để tự cấu hình build/start command và khai báo sẵn các biến môi trường cần điền (không chứa giá trị thật của key — chỉ khai tên biến).
- Đã kiểm tra `codebase/backend/.env` **không** bị commit vào git (nằm đúng trong `.gitignore`, pattern `*.env`) — key hiện tại của bạn an toàn, chưa từng lộ lên GitHub.
- CORS backend đang mở `allow_origins=["*"]` — cố tình để vậy cho đơn giản lúc demo (frontend gọi từ bất kỳ domain nào cũng được), không cần chỉnh gì thêm để deploy chạy được.
