"""Pydantic models for request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PartnerMeta(BaseModel):
    partner_id: str
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    market: Optional[str] = None
    bq_partner_id: Optional[str] = None
    current_state: Optional[str] = None
    do_not_message: int = 0
    dnm_reason: Optional[str] = None
    excluded_campaigns: Optional[list[str]] = None
    campaigns: Optional[list[str]] = None


class ConversationSummary(BaseModel):
    partner_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    last_direction: Optional[str] = None
    campaign_id: Optional[str] = None
    market: Optional[str] = None
    unread: bool = False
    draft_status: Optional[str] = None


class Message(BaseModel):
    id: str
    direction: str
    content: str
    timestamp: str
    campaign_id: Optional[str] = None
    media_urls: Optional[list[str]] = None
    classified_intent: Optional[str] = None
    draft_status: Optional[str] = None
    draft_content: Optional[str] = None


class SendRequest(BaseModel):
    conversation_id: str
    message: str
    team_id: int = 66423


class BatchSendRequest(BaseModel):
    campaign_name: str
    team_id: int = 66423
    campaign_context: Optional[str] = None
    auto_respond_enabled: bool = False
    drafts: list[dict]


class DraftRequest(BaseModel):
    partner_id: str
    reply_id: Optional[str] = None


class QueryRequest(BaseModel):
    sql: Optional[str] = None
    campaign: Optional[str] = None
    force_refresh: bool = False


class ExcludeRequest(BaseModel):
    reason: str


class CampaignExcludeRequest(BaseModel):
    campaign_id: str


class TokenUpdateRequest(BaseModel):
    token: str


class SettingUpdateRequest(BaseModel):
    key: str
    value: str


class MetricsParams(BaseModel):
    days: int = 7
    campaign_id: Optional[str] = None
