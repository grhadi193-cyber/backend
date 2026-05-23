from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


# ── Channel ─────────────────────────────────────────────────────────────────

class ChannelOut(BaseModel):
    id: int
    name: str
    name_display: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelCreateIn(BaseModel):
    name: str
    is_active: bool = True
    config: Dict[str, Any] = {}


class ChannelUpdateIn(BaseModel):
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


# ── Template ────────────────────────────────────────────────────────────────

class TemplateOut(BaseModel):
    id: int
    event_type: str
    event_type_display: str
    channel_id: int
    channel_name: str
    subject: str
    template_text: str
    is_active: bool
    description: str
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateCreateIn(BaseModel):
    event_type: str
    channel_id: int
    template_text: str
    subject: str = ""
    is_active: bool = True
    description: str = ""


class TemplateUpdateIn(BaseModel):
    event_type: Optional[str] = None
    channel_id: Optional[int] = None
    template_text: Optional[str] = None
    subject: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


# ── Log ─────────────────────────────────────────────────────────────────────

class LogOut(BaseModel):
    id: str
    event_type: str
    event_type_display: str
    channel_name: str
    recipient: str
    rendered_message: str
    subject: str
    status: str
    status_display: str
    error_message: str
    sent_at: Optional[datetime] = None
    retry_count: int
    created_at: datetime
    user_phone: Optional[str] = None
    order_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class LogListOut(BaseModel):
    count: int
    page: int
    page_size: int
    total_pages: int
    results: List[LogOut]


# ── Queue ───────────────────────────────────────────────────────────────────

class QueueOut(BaseModel):
    id: str
    event_type: str
    recipient: str
    status: str
    retry_count: int
    error_message: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QueueListOut(BaseModel):
    count: int
    page: int
    page_size: int
    total_pages: int
    results: List[QueueOut]


# ── Variables Info ──────────────────────────────────────────────────────────

class VariablesOut(BaseModel):
    event_type: Optional[str] = None
    variables: List[str] = []
    all_events: Optional[Dict[str, List[str]]] = None


class EventTypeChoice(BaseModel):
    value: str
    label: str


class EventTypesOut(BaseModel):
    choices: List[EventTypeChoice]


# ── Send Test ───────────────────────────────────────────────────────────────

class SendTestIn(BaseModel):
    template_id: int
    phone_number: str
    extra_context: Dict[str, str] = {}


class PreviewTemplateIn(BaseModel):
    template_id: int
    extra_context: Dict[str, str] = {}
