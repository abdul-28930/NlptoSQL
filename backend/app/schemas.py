from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


RoleLiteral = Literal["user", "assistant", "system"]


class UserOut(BaseModel):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BootstrapResponse(BaseModel):
    user_id: int


class SchemaBase(BaseModel):
    name: str
    description: Optional[str] = None
    raw_schema: str


class SchemaCreate(SchemaBase):
    pass


class SchemaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    raw_schema: Optional[str] = None


class SchemaOut(SchemaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    title: Optional[str] = None
    schema_id: Optional[int] = None


class SessionCreate(SessionBase):
    pass


class SessionOut(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: RoleLiteral
    content: str


class MessageCreate(BaseModel):
    content: str


class MessageOut(MessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    sql: str
    explanation: Optional[str] = None
    raw_model_output: str

