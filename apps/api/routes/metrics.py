"""Rota de métricas e dashboard."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.integrations.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


async def _query_metrics() -> dict:
    """Busca métricas do Supabase."""
    client = get_supabase_client()
    now = datetime.utcnow()
    last_24h = (now - timedelta(hours=24)).isoformat()

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


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard visual de métricas do SDR Agent."""
    metrics = await _query_metrics()

    funnel_states = [
        ("NEW", "Novos", "#6366f1"),
        ("QUALIFYING", "Qualificando", "#8b5cf6"),
        ("WAITING_PRIORITY_CONFIRMATION", "Prioridade", "#a78bfa"),
        ("WAITING_FIT_CONFIRMATION", "Fit", "#c084fc"),
        ("WAITING_TIME", "Horário", "#e879f9"),
        ("BOOKING_IN_PROGRESS", "Agendando", "#f472b6"),
        ("SCHEDULED", "Agendado ✅", "#22c55e"),
        ("CLOSED", "Fechado", "#10b981"),
        ("NO_MONEY", "Sem Budget", "#ef4444"),
    ]

    funnel_html = ""
    for state, label, color in funnel_states:
        count = metrics.get(f"leads_{state.lower()}", 0)
        pct = round((count / max(metrics.get("total_leads", 1), 1)) * 100)
        funnel_html += f"""
        <div class="funnel-row">
            <div class="funnel-bar" style="width:{max(pct, 5)}%;background:{color};">
                <span class="funnel-label">{label}</span>
                <span class="funnel-count">{count}</span>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SDR Agent — Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #0f0f23;
            color: #e2e8f0;
            padding: 2rem;
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #6366f1, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: #94a3b8; margin-bottom: 2rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: #1e1e3f;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #2d2d5f;
        }}
        .card-label {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .card-value {{ font-size: 2rem; font-weight: 700; margin-top: 0.5rem; }}
        .card-value.green {{ color: #22c55e; }}
        .card-value.purple {{ color: #a78bfa; }}
        .card-value.blue {{ color: #60a5fa; }}
        .card-value.yellow {{ color: #fbbf24; }}
        .funnel-section {{
            background: #1e1e3f;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #2d2d5f;
            margin-bottom: 2rem;
        }}
        .funnel-section h2 {{ margin-bottom: 1rem; font-size: 1.2rem; }}
        .funnel-row {{ margin-bottom: 0.5rem; }}
        .funnel-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            min-width: 80px;
            transition: width 0.5s ease;
        }}
        .funnel-label {{ font-weight: 600; }}
        .funnel-count {{ font-weight: 700; }}
        .footer {{ color: #475569; font-size: 0.8rem; margin-top: 2rem; text-align: center; }}
    </style>
</head>
<body>
    <h1>📊 SDR Agent Dashboard</h1>
    <p class="subtitle">Métricas em tempo real</p>

    <div class="grid">
        <div class="card">
            <div class="card-label">Total Leads</div>
            <div class="card-value purple">{metrics.get("total_leads", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Últimas 24h</div>
            <div class="card-value blue">{metrics.get("leads_last_24h", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Conversas Ativas</div>
            <div class="card-value yellow">{metrics.get("active_conversations", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Agendamentos</div>
            <div class="card-value green">{metrics.get("total_bookings", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Taxa Conversão</div>
            <div class="card-value green">{metrics.get("conversion_rate", 0)}%</div>
        </div>
        <div class="card">
            <div class="card-label">Msgs (24h)</div>
            <div class="card-value blue">{metrics.get("messages_last_24h", 0)}</div>
        </div>
        <div class="card">
            <div class="card-label">Follow-ups Pendentes</div>
            <div class="card-value yellow">{metrics.get("pending_follow_ups", 0)}</div>
        </div>
    </div>

    <div class="funnel-section">
        <h2>🔽 Funil de Conversão</h2>
        {funnel_html}
    </div>

    <div class="footer">
        SDR Agent v0.1.0 — Atualizado em {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
        &bull; <a href="/metrics" style="color:#6366f1;">JSON</a>
        &bull; <a href="/docs" style="color:#6366f1;">API Docs</a>
    </div>

    <script>setTimeout(() => location.reload(), 30000);</script>
</body>
</html>"""

    return HTMLResponse(content=html)
