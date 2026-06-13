from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Password, PasswordShare, SharePermission, Team, TeamMember, User
from auth import verify_password, get_current_user
from encryption import decrypt, encrypt
from schemas import (
    PasswordCreate,
    PasswordListItem,
    PasswordReveal,
    PasswordUpdate,
    RevealRequest,
    ShareCreate,
    ShareOut,
    SharePermission as SharePermissionSchema,
)

router = APIRouter(prefix="/api/passwords", tags=["passwords"])


def _can_access(user: User, password: Password) -> bool:
    if user.is_admin():
        return True
    if password.owner_id == user.id:
        return True
    return any(s.recipient_id == user.id for s in password.shares)


def _can_modify(user: User, password: Password) -> bool:
    if user.is_admin():
        return True
    if password.owner_id == user.id:
        return True
    return any(
        s.recipient_id == user.id and s.permission == SharePermission.WRITE
        for s in password.shares
    )


def _can_share(user: User, password: Password) -> bool:
    return _can_modify(user, password)


def _to_list_item(p: Password, viewer: User) -> dict:
    my_share = next((s for s in p.shares if s.recipient_id == viewer.id), None)
    return {
        "id": p.id,
        "account_username": p.account_username,
        "service": p.service,
        "description": p.description,
        "url": p.url,
        "owner": p.owner,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "shared": p.owner_id != viewer.id,
        "shared_with": [s.recipient for s in p.shares if s.recipient is not None],
        "my_permission": my_share.permission.value if my_share else None,
    }


@router.get("", response_model=List[PasswordListItem])
def list_passwords(
    account_username: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    owner_email: Optional[str] = Query(None),
    include_shared: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    stmt = (
        select(Password)
        .options(selectinload(Password.shares), selectinload(Password.owner))
        .order_by(Password.service.asc(), Password.account_username.asc())
    )

    if not current.is_admin():
        if include_shared:
            shared_ids = (
                select(PasswordShare.password_id)
                .where(PasswordShare.recipient_id == current.id)
                .scalar_subquery()
            )
            stmt = stmt.where(or_(Password.owner_id == current.id, Password.id.in_(shared_ids)))
        else:
            stmt = stmt.where(Password.owner_id == current.id)

    if account_username:
        stmt = stmt.where(Password.account_username.ilike(f"%{account_username}%"))
    if service:
        stmt = stmt.where(Password.service.ilike(f"%{service}%"))
    if description:
        stmt = stmt.where(Password.description.ilike(f"%{description}%"))
    if owner_email:
        stmt = stmt.join(User, User.id == Password.owner_id).where(
            User.email.ilike(f"%{owner_email}%")
        )

    stmt = stmt.offset(offset).limit(limit)
    rows = db.execute(stmt).scalars().unique().all()
    return [_to_list_item(p, current) for p in rows]


@router.get("/{password_id}", response_model=PasswordListItem)
def get_password(
    password_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_access(current, p):
        raise HTTPException(403, "Non sei autorizzato")
    return _to_list_item(p, current)


@router.post("/vault/unlock", status_code=204)
def unlock_vault(
    payload: RevealRequest,
    current: User = Depends(get_current_user),
):
    """Verifica la password dell'utente per sbloccare l'accesso al vault."""
    if not verify_password(payload.user_password, current.password_hash):
        raise HTTPException(status_code=403, detail="Password errata")


@router.post("/{password_id}/reveal", response_model=PasswordReveal)
def reveal_password(
    password_id: int,
    payload: RevealRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Restituisce la password in chiaro. Richiede la password dell'utente per re-auth."""
    if not verify_password(payload.user_password, current.password_hash):
        raise HTTPException(status_code=403, detail="Password vault errata")

    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_access(current, p):
        raise HTTPException(403, "Non sei autorizzato")
    try:
        plain = decrypt(p.encrypted_password)
    except Exception:
        raise HTTPException(500, "Impossibile decifrare la password (chiave master errata?)")
    return PasswordReveal(id=p.id, password=plain)


@router.post("", response_model=PasswordListItem, status_code=status.HTTP_201_CREATED)
def create_password(
    payload: PasswordCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = Password(
        account_username=payload.account_username,
        service=payload.service,
        description=payload.description,
        url=payload.url,
        encrypted_password=encrypt(payload.password),
        owner_id=current.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_list_item(p, current)


@router.put("/{password_id}", response_model=PasswordListItem)
def update_password(
    password_id: int,
    payload: PasswordUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_modify(current, p):
        raise HTTPException(403, "Solo il proprietario o chi ha permesso WRITE può modificare")

    if payload.account_username is not None:
        p.account_username = payload.account_username
    if payload.service is not None:
        p.service = payload.service
    if payload.description is not None:
        p.description = payload.description
    if payload.url is not None:
        p.url = payload.url
    if payload.password:
        p.encrypted_password = encrypt(payload.password)

    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_list_item(p, current)


@router.delete("/{password_id}", status_code=204)
def delete_password(
    password_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_modify(current, p):
        raise HTTPException(403, "Solo il proprietario o un admin può eliminare")
    db.delete(p)
    db.commit()


# -------------------------------------------------------- SHARING


@router.get("/{password_id}/shares", response_model=List[ShareOut])
def list_shares(
    password_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_share(current, p):
        raise HTTPException(403, "Non hai i permessi per vedere le condivisioni")
    return p.shares


@router.post("/{password_id}/shares", response_model=List[ShareOut], status_code=201)
def add_shares(
    password_id: int,
    payload: ShareCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_share(current, p):
        raise HTTPException(403, "Non hai i permessi per condividere")

    existing = {s.recipient_id: s for s in p.shares}

    for item in payload.recipients:
        uid = item.user_id
        if uid == p.owner_id:
            continue
        perm = SharePermission(item.permission.value)
        if uid in existing:
            existing[uid].permission = perm
            db.add(existing[uid])
        else:
            recipient = db.get(User, uid)
            if not recipient:
                continue
            db.add(PasswordShare(
                password_id=p.id,
                recipient_id=uid,
                shared_by_id=current.id,
                permission=perm,
            ))

    db.commit()
    db.refresh(p)
    return p.shares


@router.post("/{password_id}/shares/team/{team_id}", response_model=List[ShareOut], status_code=201)
def share_with_team(
    password_id: int,
    team_id: int,
    permission: SharePermissionSchema = SharePermissionSchema.READ,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_share(current, p):
        raise HTTPException(403, "Non hai i permessi per condividere")

    team = db.get(Team, team_id)
    if not team or not team.is_active:
        raise HTTPException(404, "Team non trovato")

    existing = {s.recipient_id: s for s in p.shares}
    perm = SharePermission(permission.value)

    for member in team.members:
        uid = member.user_id
        if uid == p.owner_id:
            continue
        if uid in existing:
            existing[uid].permission = perm
            db.add(existing[uid])
        else:
            user = db.get(User, uid)
            if not user:
                continue
            db.add(PasswordShare(
                password_id=p.id,
                recipient_id=uid,
                shared_by_id=current.id,
                permission=perm,
            ))

    db.commit()
    db.refresh(p)
    return p.shares


@router.post("/{password_id}/shares/ditta/{ditta_id}", response_model=List[ShareOut], status_code=201)
def share_with_ditta(
    password_id: int,
    ditta_id: int,
    permission: SharePermissionSchema = SharePermissionSchema.READ,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_share(current, p):
        raise HTTPException(403, "Non hai i permessi per condividere")

    ditta_users = (
        db.query(User)
        .filter(User.ditta_id == ditta_id, User.id != p.owner_id)
        .all()
    )

    existing = {s.recipient_id: s for s in p.shares}
    perm = SharePermission(permission.value)

    for u in ditta_users:
        if u.id in existing:
            existing[u.id].permission = perm
            db.add(existing[u.id])
        else:
            db.add(PasswordShare(
                password_id=p.id,
                recipient_id=u.id,
                shared_by_id=current.id,
                permission=perm,
            ))

    db.commit()
    db.refresh(p)
    return p.shares


@router.delete("/{password_id}/shares/{recipient_id}", status_code=204)
def remove_share(
    password_id: int,
    recipient_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    p = db.get(Password, password_id)
    if not p:
        raise HTTPException(404, "Password non trovata")
    if not _can_share(current, p):
        raise HTTPException(403, "Non hai i permessi per revocare la condivisione")
    share = (
        db.query(PasswordShare)
        .filter(PasswordShare.password_id == p.id, PasswordShare.recipient_id == recipient_id)
        .first()
    )
    if not share:
        raise HTTPException(404, "Condivisione non trovata")
    db.delete(share)
    db.commit()
