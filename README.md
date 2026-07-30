# ASHANTI REGIONAL SRC INFORMATION MANAGEMENT SYSTEM
## FastAPI Backend API & Services

Version: **4.2**  
Architecture: **Router → Service → Repository → Database**

---

## 🚀 Overview

The **Ashanti Regional SRC Information Management System** is a platform enabling secure student support, institutional communication, anonymous complaint handling, targeted broadcast notifications, event scheduling, and pre-provisioned student account management across senior high schools in the Ashanti Region and Ghana.

---

## 🏗 System Architecture

```text
┌────────────────────────────────────────────┐
│        ASHANTI REGIONAL SRC                │
│ INFORMATION MANAGEMENT SYSTEM              │
└────────────────────────────────────────────┘

Frontend (Vercel)
https://arsrc.vercel.app
            │
            │ HTTPS API Calls
            ▼
Backend (Render)
https://<your-render-service>.onrender.com
            │
            ▼
Render PostgreSQL
```

---

## 🔑 Key Features

1. **Pre-Provisioned Student Accounts**: Student accounts are created with institutional IDs (e.g. `PC-0001`, `OW-0001`) and temporary passwords. Public self-registration returns `HTTP 403 Forbidden`.
2. **First-Time Password Change Enforcement**: Backend strictly blocks access to protected endpoints with `PASSWORD_CHANGE_REQUIRED` (HTTP 403) until students complete `PATCH /api/v1/auth/change-password`.
3. **Multi-Scope Complaints & Tracking**: Students file anonymous or identified complaints with secure case ID tracking (`GES-2026-XXXXXX`).
4. **Targeted Broadcasts**: Regional and school officials publish global, regional, or school-scoped broadcasts.
5. **Events Management**: Schedule and manage regional/school events with automated student notification dispatchers.
6. **Production Health Check**: Exposed at `GET /health` and `GET /api/v1/health`.

---

## ⚙️ Environment Variables

Create a `backend/.env` file based on `.env.example`:

```env
PROJECT_NAME="ASHANTI REGIONAL SRC INFORMATION MANAGEMENT SYSTEM"
API_V1_STR="/api/v1"
ENVIRONMENT="development"

# CORS Configuration (Comma-separated)
CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,https://arsrc.vercel.app"

# Security Configuration
SECRET_KEY="c9afdf545ae770b286da10431a47b75f9b69f065e1ab3abadd0a3e3ff55ca726"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
DATABASE_URL="postgresql://username:password@hostname:5432/arsrc_db"
```

---

## 🧪 Local Development Setup

1. **Activate Virtual Environment**:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   ```

2. **Run Alembic Schema Migrations**:
   ```powershell
   alembic upgrade head
   ```

3. **Seed Development Database**:
   ```powershell
   python seed.py --reset
   ```

4. **Start Development API Server**:
   ```powershell
   uvicorn main:app --reload
   ```

5. **Access Interactive Swagger Documentation**:
   Navigate to `http://127.0.0.1:8000/docs` in your browser.

---

## 🚀 Render Deployment (Production)

When deploying to Render using the included [render.yaml](file:///c:/Users/Bill/Desktop/GES-Student-Support-Platform/render.yaml) blueprint:

- **Build Command**:
  ```bash
  pip install -r requirements.txt && alembic upgrade head
  ```
- **Start Command**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### Manual Admin Account Bootstrap in Production
To create your initial production administrator without hardcoded passwords or public registration:
```bash
python bootstrap_admin.py
```
Enter the administrator's name, email, and password when prompted.
