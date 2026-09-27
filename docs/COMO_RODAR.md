# Como rodar o projeto completo

## Terminal 1 — backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `backend/.env` e defina `JWT_SECRET_KEY` e `ADMIN_PASSWORD`. Para Supabase, também defina `DATABASE_URL` usando **Connect > Session pooler**.

Depois:

```powershell
python -m app.seed
uvicorn app.main:app --reload
```

## Terminal 2 — frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Abra `http://localhost:5173` e entre com `ADMIN_EMAIL` e `ADMIN_PASSWORD` definidos antes do seed.
