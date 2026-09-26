from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def registrar_auditoria(
    db: Session,
    *,
    user: User | None,
    acao: str,
    recurso: str,
    request: Request | None = None,
    recurso_id: str | int | None = None,
    detalhes: dict | None = None,
):
    registro = AuditLog(
        user_id=user.id if user else None,
        acao=acao,
        recurso=recurso,
        recurso_id=str(recurso_id) if recurso_id is not None else None,
        metodo=request.method if request else None,
        caminho=request.url.path if request else None,
        detalhes=detalhes,
    )
    db.add(registro)
    db.commit()
