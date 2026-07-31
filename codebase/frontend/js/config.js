// =====================================================================
// Deployment config — the ONE place to point the frontend at your live
// backend URL after deploying it (Render, HF Spaces, etc.).
//
// Local dev (opening via 127.0.0.1/localhost) auto-uses the local backend,
// so this file does NOT need editing to keep developing on your machine.
// Once your backend is deployed, replace PROD_API_BASE below with its real
// URL (e.g. "https://vlearn-ai-tutor-backend.onrender.com") and redeploy
// the frontend (or just push — Cloudflare Pages/Netlify auto-redeploy).
// =====================================================================
const PROD_API_BASE = "https://REPLACE_WITH_YOUR_BACKEND_URL.onrender.com";

window.APP_CONFIG = {
  API_BASE:
    location.hostname === "localhost" || location.hostname === "127.0.0.1"
      ? "http://127.0.0.1:8000"
      : PROD_API_BASE,
};
