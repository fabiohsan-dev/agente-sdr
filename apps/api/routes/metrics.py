"""Rota de métricas e dashboard."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.integrations.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

templates_dir = Path(__file__).parent.parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


async def _query_metrics() -> dict:
    """Busca métricas do Supabase."""
    client = get_supabase_client()
    now = datetime.utcnow()
    last_24h = (now - timedelta(hours=24)).isoformat()
    # last_7d = (now - timedelta(days=7)).isoformat()

    metrics = {}

    try:
        # Total de leads
        leads = client.table("leads").select("id", count="exact").execute()
        metrics["total_leads"] = leads.count or 0

        # Leads por estado
        for state in [
            "NEW",
            "QUALIFYING",
            "WAITING_PRIORITY_CONFIRMATION",
            "WAITING_FIT_CONFIRMATION",
            "WAITING_TIME",
            "BOOKING_IN_PROGRESS",
            "SCHEDULED",
            "POST_BOOKING_PENDING_MATERIALS",
            "POST_BOOKING_PENDING_CHECKLIST",
            "NO_MONEY",
            "CLOSED",
        ]:
            result = (
                client.table("leads")
                .select("id", count="exact")
                .eq("current_state", state)
                .execute()
            )
            metrics[f"leads_{state.lower()}"] = result.count or 0

        # Leads últimas 24h
        recent = (
            client.table("leads").select("id", count="exact").gte("created_at", last_24h).execute()
        )
        metrics["leads_last_24h"] = recent.count or 0

        # Mensagens últimas 24h
        msgs = (
            client.table("messages")
            .select("id", count="exact")
            .gte("created_at", last_24h)
            .execute()
        )
        metrics["messages_last_24h"] = msgs.count or 0

        # Conversas ativas
        convs = (
            client.table("conversations")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
        )
        metrics["active_conversations"] = convs.count or 0

        # Bookings agendados
        bookings = client.table("bookings").select("id", count="exact").execute()
        metrics["total_bookings"] = bookings.count or 0

        # Taxa de conversão (leads → scheduled)
        scheduled = metrics.get("leads_scheduled", 0)
        total = metrics.get("total_leads", 1)
        metrics["conversion_rate"] = round((scheduled / max(total, 1)) * 100, 1)

        # Follow-ups pendentes
        follows = (
            client.table("follow_jobs")
            .select("id", count="exact")
            .eq("status", "pending")
            .execute()
        )
        metrics["pending_follow_ups"] = follows.count or 0

    except Exception as e:
        logger.error(f"Erro ao buscar métricas: {e}")
        metrics["error"] = str(e)

    return metrics


@router.get("/", response_model=dict)
async def get_metrics():
    """Retorna métricas em JSON."""
    return await _query_metrics()


async def _get_historical_data(days: int = 7) -> dict:
    """Busca dados historicos agrupados por dia para os charts."""
    client = get_supabase_client()
    now = datetime.utcnow()
    metrics = {"labels": [], "leads_data": [], "bookings_data": []}

    # Prepopula dias
    counts_by_day = {}
    for i in range(days-1, -1, -1):
        day_str = (now - timedelta(days=i)).strftime('%b %d')
        counts_by_day[day_str] = {"leads": 0, "bookings": 0}
        metrics["labels"].append(day_str)

    start_date = (now - timedelta(days=days)).isoformat()

    try:
        # Leads por dia
        leads = client.table("leads").select("created_at").gte("created_at", start_date).execute()
        for item in leads.data:
            dt = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            day_str = dt.strftime('%b %d')
            if day_str in counts_by_day:
                counts_by_day[day_str]["leads"] += 1

        # Bookings por dia
        bookings = client.table("bookings").select("created_at").gte("created_at", start_date).execute()
        for item in bookings.data:
            dt = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            day_str = dt.strftime('%b %d')
            if day_str in counts_by_day:
                counts_by_day[day_str]["bookings"] += 1

        for label in metrics["labels"]:
            metrics["leads_data"].append(counts_by_day[label]["leads"])
            metrics["bookings_data"].append(counts_by_day[label]["bookings"])

    except Exception as e:
        logger.error(f"Erro ao buscar historico: {e}")

    return metrics

async def _get_recent_leads(limit: int = 5) -> list:
    """Busca leads recentes ativos (excluindo CLOSED e NO_MONEY)."""
    client = get_supabase_client()
    try:
        result = (
            client.table("leads")
            .select("name, phone, current_state, created_at, updated_at")
            .neq("current_state", "CLOSED")
            .neq("current_state", "NO_MONEY")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Erro ao buscar leads recentes: {e}")
        return []

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard visual de métricas do SDR Agent com Jinja2 e Chart.js."""
    metrics = await _query_metrics()
    history = await _get_historical_data(days=7)
    recent_leads = await _get_recent_leads(limit=5)

    # Preparando dados do funil (donut chart config)
    funnel_states = [
        ("N" if s == "NEW" else s[:5], s, metrics.get(f"leads_{s.lower()}", 0)) for s in
        ["NEW", "QUALIFYING", "WAITING_TIME", "BOOKING_IN_PROGRESS", "SCHEDULED"]
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "metrics": metrics,
            "history": history,
            "recent_leads": recent_leads,
            "funnel_states": funnel_states,
            "last_update": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
    )
