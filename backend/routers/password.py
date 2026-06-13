from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import SelfUpdateRequest, UserOut
from auth import verify_password, hash_password, get_current_user
from audit import log_password_event

router = APIRouter(prefix="/api/users", tags=["password"])


@router.put("/me", response_model=UserOut)
def update_me(
    payload: SelfUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.nuova_password:
        if not payload.password_attuale:
            raise HTTPException(status_code=400, detail="Inserisci la password attuale per cambiarla.")
        if not verify_password(payload.password_attuale, current_user.password_hash):
            log_password_event(
                action="self_change", actor_id=current_user.id, actor_email=current_user.email,
                target_id=current_user.id, target_email=current_user.email,
                request=request, success=False, reason="wrong_current_password",
            )
            raise HTTPException(status_code=400, detail="Password attuale non corretta.")
        current_user.password_hash = hash_password(payload.nuova_password)
        log_password_event(
            action="self_change", actor_id=current_user.id, actor_email=current_user.email,
            target_id=current_user.id, target_email=current_user.email, request=request,
        )
    if payload.nome is not None:
        current_user.nome = payload.nome
    if payload.cognome is not None:
        current_user.cognome = payload.cognome
    db.commit()
    db.refresh(current_user)
    return current_user
