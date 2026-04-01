"""Enums do domínio."""

from enum import Enum


class LeadState(str, Enum):
    """Estados possíveis de um lead."""

    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    WAITING_PRIORITY_CONFIRMATION = "WAITING_PRIORITY_CONFIRMATION"
    WAITING_FIT_CONFIRMATION = "WAITING_FIT_CONFIRMATION"
    WAITING_TIME = "WAITING_TIME"
    WAITING_EMAIL = "WAITING_EMAIL"
    BOOKING_IN_PROGRESS = "BOOKING_IN_PROGRESS"
    SCHEDULED = "SCHEDULED"
    POST_BOOKING_PENDING_MATERIALS = "POST_BOOKING_PENDING_MATERIALS"
    POST_BOOKING_PENDING_CHECKLIST = "POST_BOOKING_PENDING_CHECKLIST"
    NO_MONEY = "NO_MONEY"
    CLOSED = "CLOSED"
    PAUSED_BY_HUMAN = "PAUSED_BY_HUMAN"


class OwnerMode(str, Enum):
    """Modo de controle do lead."""

    AGENT = "agent"
    HUMAN = "human"


class MessageType(str, Enum):
    """Tipos de mensagem."""

    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"


class MessageDirection(str, Enum):
    """Direção da mensagem."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MediaType(str, Enum):
    """Tipos de mídia."""

    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class MediaStatus(str, Enum):
    """Status do processamento de mídia."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    """Tipos de evento."""

    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    STATE_CHANGED = "state_changed"
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled"
    FOLLOW_SCHEDULED = "follow_scheduled"
    FOLLOW_CANCELLED = "follow_cancelled"
    MATERIALS_SENT = "materials_sent"
    CHECKLIST_SENT = "checklist_sent"
    HANDOFF_TO_HUMAN = "handoff_to_human"
    HANDOFF_TO_AGENT = "handoff_to_agent"
    ERROR = "error"


class FollowJobStatus(str, Enum):
    """Status de job de follow-up."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
