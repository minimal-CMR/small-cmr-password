import enum
from sqlalchemy import (
    Column, Integer, String, TIMESTAMP, Text, ForeignKey, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """Replica locale di users — gestita da small-cmr-base."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    nome          = Column(String(100), nullable=False)
    cognome       = Column(String(100), nullable=False)
    email         = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    azienda       = Column(String(255), default="")
    ditta_id      = Column(Integer, nullable=True)
    ruolo         = Column(String(200), nullable=False, default="opts")
    created_at    = Column(TIMESTAMP, server_default=func.now())

    def get_ruoli(self) -> list:
        return [r.strip() for r in (self.ruolo or "opts").split(",") if r.strip()]

    def is_admin(self) -> bool:
        return "admin" in self.get_ruoli()

    def has_role(self, *roles: str) -> bool:
        if self.is_admin():
            return True
        return any(r in self.get_ruoli() for r in roles)


class Team(Base):
    """Replica locale di teams — gestita da small-cmr-base. Solo lettura."""
    __tablename__ = "teams"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active   = Column(Integer, nullable=False, default=1)
    created_at  = Column(TIMESTAMP, server_default=func.now())

    members = relationship("TeamMember", back_populates="team", lazy="selectin")


class TeamMember(Base):
    __tablename__ = "team_members"

    id       = Column(Integer, primary_key=True)
    team_id  = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    team = relationship("Team", back_populates="members")
    user = relationship("User")


class SharePermission(str, enum.Enum):
    READ = "read"
    WRITE = "write"


class Password(Base):
    """Record di password salvato nel vault, cifrato AES-256-GCM."""
    __tablename__ = "passwords"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    account_username   = Column(String(255), nullable=False, index=True)
    encrypted_password = Column(Text, nullable=False)
    service            = Column(String(255), nullable=False, index=True)
    description        = Column(Text, nullable=True)
    url                = Column(String(500), nullable=True)
    owner_id           = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at         = Column(TIMESTAMP, server_default=func.now())
    updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    owner  = relationship("User", lazy="joined", foreign_keys=[owner_id])
    shares = relationship("PasswordShare", back_populates="password",
                          cascade="all, delete-orphan", lazy="selectin")


class PasswordShare(Base):
    __tablename__ = "password_shares"
    __table_args__ = (UniqueConstraint("password_id", "recipient_id", name="uq_share_password_recipient"),)

    id            = Column(Integer, primary_key=True, autoincrement=True)
    password_id   = Column(Integer, ForeignKey("passwords.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_by_id  = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    permission    = Column(Enum(SharePermission), nullable=False, default=SharePermission.READ)
    created_at    = Column(TIMESTAMP, server_default=func.now())

    password  = relationship("Password", back_populates="shares")
    recipient = relationship("User", foreign_keys=[recipient_id], lazy="joined")
    shared_by = relationship("User", foreign_keys=[shared_by_id], lazy="joined")
