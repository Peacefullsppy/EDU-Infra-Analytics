from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from .core import engine, settings, validate_startup
from .routes import router

validate_startup()
app = FastAPI(title="EDU-Infra Analytics 1.6", description="API para infraestrutura escolar e aceite versionado de Termos e Condições", version="1.6.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-Computer-ID", "X-Agent-Token"])


@app.middleware("http")
async def headers(request: Request, call_next):
    if settings.require_https and request.url.scheme != "https" and request.headers.get("x-forwarded-proto") != "https" and request.url.path != "/health":
        return JSONResponse({"detail": "HTTPS obrigatório"}, status_code=426)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        raise HTTPException(503, "Banco indisponível")


app.include_router(router)
