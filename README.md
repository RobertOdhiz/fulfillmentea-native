## Fulfillmentea Native

### Backend (FastAPI + SQLite)

Windows PowerShell commands:

```powershell
# From repo root
python -m venv backend\.venv
backend\.venv\Scripts\pip.exe install -U pip
backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Bootstrap first admin user:

```http
POST http://localhost:8000/auth/bootstrap
Content-Type: application/json
{
  "full_name": "Admin User",
  "phone": "+15550000000",
  "email": "admin@example.com",
  "role": "SUPER_ADMIN",
  "password": "ChangeMe123!"
}
```

Login to get token:

```http
POST http://localhost:8000/auth/login
Content-Type: application/json
{
  "phone": "+15550000000",
  "password": "ChangeMe123!"
}
```

- IDs are UUIDv4 strings everywhere now.
- Swagger UI supports bearer authorization: open `http://localhost:8000/docs`, click Authorize, type `Bearer <token>` or just paste the token (the UI uses Bearer scheme automatically).

### Frontend (Expo)

```powershell
# From repo root
cd mobile
npm install
npx expo start --tunnel
```

Configure `mobile/app.json` to set API base URL for devices.

### Dashboard (Streamlit)

```powershell
# From repo root
python -m venv dashboard\.venv
dashboard\.venv\Scripts\pip.exe install -U pip
dashboard\.venv\Scripts\pip.exe install -r dashboard\requirements.txt
$env:API_BASE_URL = "http://localhost:8000"
dashboard\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

- Only roles `SUPER_ADMIN`, `ADMIN`, and `MANAGER` can access the dashboard.
- Staff management is visible to `SUPER_ADMIN` and `ADMIN`.
