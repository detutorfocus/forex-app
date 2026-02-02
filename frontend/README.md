# Forex Frontend (React + DRF)

This is a modern React frontend (Vite + TypeScript + Tailwind + TanStack Query) for your Django/DRF forex project.

## 1) Setup

```bash
cd forex-frontend
npm install
cp .env .env
npm run dev
```

Set `VITE_API_BASE_URL` to your Django base URL (default: http://127.0.0.1:8000).

## 2) Backend endpoints assumed

Auth:
- POST `/api/token/` and `/api/token/refresh/` (SimpleJWT) **preferred**
- fallback: POST `/api/auth/login/` (your current endpoint returns only a message; frontend stores a DEV_SESSION)

Trading:
- GET `/api/trading/live/positions/`
- GET `/api/trading/live/orders/`
- GET `/api/trading/live/history/`
- GET `/api/trading/audit/export?format=json|csv`
- GET `/api/trading/audit/verify`

AI Assistant:
- POST `/ai/alex/analyze/`

If any differ in your backend, change `src/services/*.ts` only.

## 3) Recommended DRF settings

Enable CORS so React can call your API:

- install: `pip install django-cors-headers`
- add `corsheaders` to INSTALLED_APPS
- add `corsheaders.middleware.CorsMiddleware` near the top of MIDDLEWARE
- set: `CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5173"]`
