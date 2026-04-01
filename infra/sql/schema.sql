-- ============================================
-- SDR AGENT - Schema do Supabase
-- ============================================
-- Executar no SQL Editor do Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ENUMS
-- ============================================

CREATE TYPE lead_state AS ENUM (
    'NEW',
    'QUALIFYING',
    'WAITING_PRIORITY_CONFIRMATION',
    'WAITING_FIT_CONFIRMATION',
    'WAITING_TIME',
    'WAITING_EMAIL',
    'BOOKING_IN_PROGRESS',
    'SCHEDULED',
    'POST_BOOKING_PENDING_MATERIALS',
    'POST_BOOKING_PENDING_CHECKLIST',
    'NO_MONEY',
    'CLOSED',
    'PAUSED_BY_HUMAN'
);

CREATE TYPE owner_mode AS ENUM (
    'agent',
    'human'
);

CREATE TYPE message_type AS ENUM (
    'text',
    'audio',
    'image'
);

CREATE TYPE message_direction AS ENUM (
    'inbound',
    'outbound'
);

CREATE TYPE media_type AS ENUM (
    'audio',
    'image',
    'video',
    'document'
);

CREATE TYPE media_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed'
);

CREATE TYPE event_type AS ENUM (
    'message_received',
    'message_sent',
    'state_changed',
    'booking_created',
    'booking_cancelled',
    'booking_rescheduled',
    'follow_scheduled',
    'follow_cancelled',
    'materials_sent',
    'checklist_sent',
    'handoff_to_human',
    'handoff_to_agent',
    'error'
);

CREATE TYPE follow_job_status AS ENUM (
    'pending',
    'completed',
    'cancelled',
    'failed'
);

-- ============================================
-- TABLE: leads
-- ============================================

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificação
    name TEXT,
    email TEXT,
    phone TEXT,
    company TEXT,
    
    -- Estado atual
    current_state lead_state NOT NULL DEFAULT 'NEW',
    owner_mode owner_mode NOT NULL DEFAULT 'agent',
    
    -- Controle de fluxo
    has_booking BOOLEAN NOT NULL DEFAULT FALSE,
    materials_sent BOOLEAN NOT NULL DEFAULT FALSE,
    checklist_sent BOOLEAN NOT NULL DEFAULT FALSE,
    no_money_flag BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Follow-up
    follow_step INTEGER NOT NULL DEFAULT 0,  -- Passo atual da cadência (0-4)
    follow_scheduled_at TIMESTAMPTZ,
    follow_cancelled_at TIMESTAMPTZ,
    
    -- Metadados
    source TEXT,
    tags TEXT[],
    custom_fields JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT leads_email_unique UNIQUE (email),
    CONSTRAINT leads_phone_unique UNIQUE (phone)
);

CREATE INDEX idx_leads_current_state ON leads(current_state);
CREATE INDEX idx_leads_owner_mode ON leads(owner_mode);
CREATE INDEX idx_leads_created_at ON leads(created_at);

-- ============================================
-- TABLE: conversations
-- ============================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Identificação da sessão
    session_id TEXT NOT NULL,
    
    -- Estado
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Metadados
    channel TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
);

CREATE INDEX idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_is_active ON conversations(is_active);

-- ============================================
-- TABLE: messages
-- ============================================

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Conteúdo
    message_type message_type NOT NULL DEFAULT 'text',
    direction message_direction NOT NULL,
    content TEXT,
    
    -- Mídia (quando aplicável)
    media_url TEXT,
    media_mime_type TEXT,
    media_filename TEXT,
    media_transcription TEXT,
    media_analysis TEXT,
    
    -- Metadados
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_direction ON messages(direction);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- ============================================
-- TABLE: events
-- ============================================

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    
    -- Tipo de evento
    event_type event_type NOT NULL,
    
    -- Detalhes
    description TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_lead_id ON events(lead_id);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_events_created_at ON events(created_at);

-- ============================================
-- TABLE: follow_jobs
-- ============================================

CREATE TABLE follow_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Agendamento
    scheduled_for TIMESTAMPTZ NOT NULL,
    
    -- Estado
    status follow_job_status NOT NULL DEFAULT 'pending',
    
    -- Motivo do follow-up
    reason TEXT,
    
    -- Metadados
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

CREATE INDEX idx_follow_jobs_lead_id ON follow_jobs(lead_id);
CREATE INDEX idx_follow_jobs_status ON follow_jobs(status);
CREATE INDEX idx_follow_jobs_scheduled_for ON follow_jobs(scheduled_for);

-- ============================================
-- TABLE: bookings
-- ============================================

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    -- ID externo do Cal.com
    calcom_booking_id INTEGER,
    
    -- Detalhes do agendamento
    title TEXT,
    description TEXT,
    
    -- Data/hora
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
    
    -- Estado
    status TEXT NOT NULL DEFAULT 'confirmed',
    cancelled_at TIMESTAMPTZ,
    rescheduled_from_id UUID REFERENCES bookings(id),
    
    -- Link
    meeting_url TEXT,
    
    -- Metadados do Cal.com
    calcom_data JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bookings_lead_id ON bookings(lead_id);
CREATE INDEX idx_bookings_calcom_booking_id ON bookings(calcom_booking_id);
CREATE INDEX idx_bookings_start_time ON bookings(start_time);
CREATE INDEX idx_bookings_status ON bookings(status);

-- ============================================
-- TABLE: media_assets
-- ============================================

CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Tipo e origem
    media_type media_type NOT NULL,
    cdn_url TEXT NOT NULL,
    mime_type TEXT,
    original_filename TEXT,
    
    -- Processamento
    transcription TEXT,
    analysis TEXT,
    status media_status NOT NULL DEFAULT 'pending',
    
    -- Metadados
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_media_assets_lead_id ON media_assets(lead_id);
CREATE INDEX idx_media_assets_conversation_id ON media_assets(conversation_id);
CREATE INDEX idx_media_assets_message_id ON media_assets(message_id);
CREATE INDEX idx_media_assets_status ON media_assets(status);

-- ============================================
-- TABLE: agent_snapshots
-- ============================================

CREATE TABLE agent_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    
    -- Estado antes/depois
    state_before lead_state,
    state_after lead_state,
    
    -- Decisão do agente
    reply_text TEXT,
    actions TEXT[],
    should_schedule_follow BOOLEAN,
    should_call_booking_tool BOOLEAN,
    should_send_materials BOOLEAN,
    should_send_checklist BOOLEAN,
    should_pause_ai BOOLEAN DEFAULT FALSE,
    
    -- Contexto
    prompt_used TEXT,
    model_used TEXT,
    tools_called JSONB DEFAULT '[]',
    
    -- Performance
    latency_ms INTEGER,
    tokens_used INTEGER,
    
    -- Erros
    error TEXT,
    
    -- Metadados
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_snapshots_lead_id ON agent_snapshots(lead_id);
CREATE INDEX idx_agent_snapshots_created_at ON agent_snapshots(created_at);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Atualizar last_message_at na conversation
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET last_message_at = NEW.created_at
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_on_message
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_last_message();

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE leads IS 'Leads e seus estados atuais';
COMMENT ON TABLE conversations IS 'Conversas por sessão';
COMMENT ON TABLE messages IS 'Mensagens trocadas (texto, áudio, imagem)';
COMMENT ON TABLE events IS 'Eventos de auditoria do sistema';
COMMENT ON TABLE follow_jobs IS 'Jobs de follow-up agendados';
COMMENT ON TABLE bookings IS 'Agendamentos via Cal.com';
COMMENT ON TABLE media_assets IS 'Arquivos de mídia em CDN (fonte de verdade)';
COMMENT ON TABLE agent_snapshots IS 'Snapshots das decisões do agente para debug';

COMMENT ON COLUMN leads.current_state IS 'Estado atual do lead no fluxo';
COMMENT ON COLUMN leads.owner_mode IS 'Quem controla: agent ou human';
COMMENT ON COLUMN leads.no_money_flag IS 'True se lead disse que não tem dinheiro';
COMMENT ON COLUMN media_assets.cdn_url IS 'URL original da CDN - fonte de verdade';
COMMENT ON COLUMN media_assets.transcription IS 'Transcrição auxiliar (não substitui original)';
COMMENT ON COLUMN media_assets.analysis IS 'Análise auxiliar (não substitui original)';
COMMENT ON COLUMN agent_snapshots.state_before IS 'Estado antes da decisão';
COMMENT ON COLUMN agent_snapshots.state_after IS 'Estado depois da decisão';
