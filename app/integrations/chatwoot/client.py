"""Cliente HTTP para a API do Chatwoot.

Responsável por enviar mensagens de volta ao Chatwoot e gerenciar contatos.
Docs: https://www.chatwoot.com/developers/api/
"""

import logging
from typing import Any

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class ChatwootClient:
    """Cliente para a API REST do Chatwoot."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.chatwoot_base_url.rstrip("/")
        self.api_token = settings.chatwoot_api_token
        self.account_id = settings.chatwoot_account_id
        self.inbox_id = settings.chatwoot_inbox_id
        self._client: httpx.AsyncClient | None = None

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "api_access_token": self.api_token,
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"{self.base_url}/api/v1/accounts/{self.account_id}",
                headers=self._headers,
                timeout=30.0,
            )
        return self._client

    # ── Mensagens ───────────────────────────────────────────

    async def send_message(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False,
    ) -> dict[str, Any]:
        """Envia mensagem para uma conversa no Chatwoot.

        Args:
            conversation_id: ID da conversa no Chatwoot
            content: Texto da mensagem
            message_type: 'outgoing' (para o contato) ou 'activity' (nota interna)
            private: Se True, envia como nota privada
        """
        client = await self._get_client()
        payload = {
            "content": content,
            "message_type": message_type,
            "private": private,
        }

        try:
            resp = await client.post(
                f"/conversations/{conversation_id}/messages",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                f"Mensagem enviada ao Chatwoot: conv={conversation_id}, "
                f"msg_id={data.get('id')}"
            )
            return data
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Erro HTTP ao enviar mensagem ao Chatwoot: {e.response.status_code} "
                f"- {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem ao Chatwoot: {e}")
            raise

    async def send_activity(
        self,
        conversation_id: int,
        content: str,
    ) -> dict[str, Any]:
        """Envia nota de atividade (visível apenas para agentes)."""
        return await self.send_message(
            conversation_id=conversation_id,
            content=content,
            message_type="outgoing",
            private=True,
        )

    # ── Contatos ────────────────────────────────────────────

    async def get_contact(self, contact_id: int) -> dict[str, Any]:
        """Busca dados de um contato."""
        client = await self._get_client()
        resp = await client.get(f"/contacts/{contact_id}")
        resp.raise_for_status()
        return resp.json()

    async def update_contact(
        self,
        contact_id: int,
        custom_attributes: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Atualiza dados de um contato (ex: estágio do funil)."""
        client = await self._get_client()
        payload: dict[str, Any] = {**kwargs}
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes

        resp = await client.put(f"/contacts/{contact_id}", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ── Conversas ───────────────────────────────────────────

    async def toggle_conversation_status(
        self,
        conversation_id: int,
        status: str = "open",
    ) -> dict[str, Any]:
        """Altera status da conversa (open, resolved, pending)."""
        client = await self._get_client()
        resp = await client.post(
            f"/conversations/{conversation_id}/toggle_status",
            json={"status": status},
        )
        resp.raise_for_status()
        return resp.json()

    async def assign_conversation(
        self,
        conversation_id: int,
        assignee_id: int | None = None,
    ) -> dict[str, Any]:
        """Atribui conversa a um agente humano."""
        client = await self._get_client()
        payload: dict[str, Any] = {}
        if assignee_id:
            payload["assignee_id"] = assignee_id
        resp = await client.post(
            f"/conversations/{conversation_id}/assignments",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Labels ──────────────────────────────────────────────

    async def add_label(
        self,
        conversation_id: int,
        label: str,
    ) -> dict[str, Any]:
        """Adiciona label à conversa."""
        client = await self._get_client()
        # Busca labels atuais
        conv_resp = await client.get(f"/conversations/{conversation_id}")
        conv_resp.raise_for_status()
        current_labels = conv_resp.json().get("labels", [])

        if label not in current_labels:
            current_labels.append(label)

        resp = await client.post(
            f"/conversations/{conversation_id}/labels",
            json={"labels": current_labels},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Cleanup ─────────────────────────────────────────────

    async def close(self):
        """Fecha o cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# ── Singleton ───────────────────────────────────────────────

_chatwoot_client: ChatwootClient | None = None


def get_chatwoot_client() -> ChatwootClient:
    """Retorna instância singleton do ChatwootClient."""
    global _chatwoot_client
    if _chatwoot_client is None:
        _chatwoot_client = ChatwootClient()
    return _chatwoot_client
