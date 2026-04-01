"""Schemas para o webhook do Chatwoot.

Modela os payloads recebidos do Chatwoot via webhook.
Docs: https://www.chatwoot.com/developers/api/#tag/Webhooks
"""

from typing import Any

from pydantic import BaseModel, Field


class ChatwootSender(BaseModel):
    """Dados do remetente da mensagem."""

    id: int | None = None
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    type: str | None = None  # "contact" ou "user"
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class ChatwootConversation(BaseModel):
    """Dados da conversa do Chatwoot."""

    id: int
    inbox_id: int | None = None
    status: str | None = None  # "open", "resolved", "pending"
    account_id: int | None = None
    additional_attributes: dict[str, Any] = Field(default_factory=dict)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    contact_inbox: dict[str, Any] = Field(default_factory=dict)


class ChatwootMessageAttachment(BaseModel):
    """Anexo de mídia na mensagem."""

    id: int | None = None
    file_type: str | None = None  # "image", "audio", "video", "file"
    data_url: str | None = None
    account_id: int | None = None


class ChatwootMessage(BaseModel):
    """Mensagem do Chatwoot vinda no webhook."""

    id: int | None = None
    content: str | None = None
    content_type: str | None = None  # "text", "input_select", etc.
    message_type: str | None = None  # "incoming", "outgoing", "activity"
    created_at: str | None = None
    private: bool = False
    source_id: str | None = None
    attachments: list[ChatwootMessageAttachment] = Field(default_factory=list)
    sender: ChatwootSender | None = None
    conversation: ChatwootConversation | None = None


class ChatwootWebhookPayload(BaseModel):
    """Payload completo do webhook do Chatwoot.

    O Chatwoot envia webhooks em vários eventos:
    - message_created
    - message_updated
    - conversation_created
    - conversation_status_changed
    - conversation_updated
    - contact_created
    - contact_updated
    """

    event: str | None = None  # "message_created", "conversation_created", etc.

    # Campos que podem vir dependendo do evento
    id: int | None = None
    content: str | None = None
    content_type: str | None = None
    message_type: str | None = None  # "incoming", "outgoing", "activity"
    created_at: str | None = None
    private: bool = False
    source_id: str | None = None
    account: dict[str, Any] = Field(default_factory=dict)
    inbox: dict[str, Any] = Field(default_factory=dict)

    # Objetos aninhados
    sender: ChatwootSender | None = None
    conversation: ChatwootConversation | None = None
    attachments: list[ChatwootMessageAttachment] = Field(default_factory=list)

    # Campos adicionais
    additional_attributes: dict[str, Any] = Field(default_factory=dict)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    content_attributes: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_incoming_message(self) -> bool:
        """Retorna True se é uma mensagem recebida do contato (não do agente)."""
        return (
            self.event == "message_created"
            and self.message_type == "incoming"
            and not self.private
        )

    @property
    def is_outgoing_message(self) -> bool:
        """Retorna True se é uma mensagem enviada pelo agente/humano."""
        return (
            self.event == "message_created"
            and self.message_type == "outgoing"
        )

    @property
    def has_media(self) -> bool:
        """Retorna True se a mensagem tem anexos de mídia."""
        return len(self.attachments) > 0

    @property
    def first_attachment_url(self) -> str | None:
        """Retorna URL do primeiro anexo, se houver."""
        if self.attachments:
            return self.attachments[0].data_url
        return None

    @property
    def first_attachment_type(self) -> str | None:
        """Retorna tipo do primeiro anexo, se houver."""
        if self.attachments:
            return self.attachments[0].file_type
        return None

    @property
    def chatwoot_conversation_id(self) -> int | None:
        """Retorna ID da conversa do Chatwoot."""
        if self.conversation:
            return self.conversation.id
        return None

    @property
    def contact_name(self) -> str | None:
        """Retorna nome do contato."""
        if self.sender:
            return self.sender.name
        return None

    @property
    def contact_email(self) -> str | None:
        """Retorna email do contato."""
        if self.sender:
            return self.sender.email
        return None

    @property
    def contact_phone(self) -> str | None:
        """Retorna telefone do contato."""
        if self.sender:
            return self.sender.phone_number
        return None
