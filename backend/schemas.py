from pydantic import BaseModel, EmailStr, ConfigDict, Field, computed_field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SelfUpdateRequest(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    password_attuale: Optional[str] = None
    nuova_password: Optional[str] = None


class UserOut(BaseModel):
    id: int
    nome: str
    cognome: str
    email: str
    azienda: Optional[str] = ""
    ditta_id: Optional[int] = None
    ruolo: str = "opts"
    created_at: Optional[datetime] = None

    @computed_field
    @property
    def ruoli(self) -> List[str]:
        return [r.strip() for r in (self.ruolo or "opts").split(",") if r.strip()]

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    id: int
    nome: str
    cognome: str
    email: str
    ditta_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class SharePermission(str, Enum):
    READ = "read"
    WRITE = "write"


class PasswordBase(BaseModel):
    account_username: str = Field(min_length=1, max_length=255)
    service: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    url: Optional[str] = Field(default=None, max_length=500)


class PasswordCreate(PasswordBase):
    password: str = Field(min_length=1, max_length=1024)


class PasswordUpdate(BaseModel):
    account_username: Optional[str] = Field(default=None, min_length=1, max_length=255)
    service: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    url: Optional[str] = Field(default=None, max_length=500)
    password: Optional[str] = Field(default=None, min_length=1, max_length=1024)


class PasswordListItem(PasswordBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner: UserPublic
    created_at: datetime
    updated_at: datetime
    shared: bool = False
    shared_with: List[UserPublic] = []
    my_permission: Optional[str] = None


class RevealRequest(BaseModel):
    user_password: str


class PasswordReveal(BaseModel):
    id: int
    password: str


class RecipientPermission(BaseModel):
    user_id: int
    permission: SharePermission = SharePermission.READ


class ShareCreate(BaseModel):
    recipients: List[RecipientPermission]


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    password_id: int
    recipient: UserPublic
    shared_by: Optional[UserPublic] = None
    permission: SharePermission = SharePermission.READ
    created_at: datetime
