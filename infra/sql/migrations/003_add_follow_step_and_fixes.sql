-- ============================================
-- Migration 003: Correções da auditoria
-- ============================================
-- Executar no SQL Editor do Supabase

-- P0: Adicionar follow_step ao lead (persistir cadência)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS follow_step INTEGER NOT NULL DEFAULT 0;

-- P1: Adicionar calcom_booking_uid ao bookings (para reschedule/cancel)
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS calcom_booking_uid TEXT;

-- P1: Adicionar should_pause_ai ao agent_snapshots (observabilidade)
ALTER TABLE agent_snapshots ADD COLUMN IF NOT EXISTS should_pause_ai BOOLEAN DEFAULT FALSE;

-- P1: Índice para buscar follow_jobs overdue (worker)
CREATE INDEX IF NOT EXISTS idx_follow_jobs_overdue
    ON follow_jobs (status, scheduled_for)
    WHERE status = 'pending';

-- P1: Índice para buscar leads com follow pendente
CREATE INDEX IF NOT EXISTS idx_leads_follow_step
    ON leads (follow_step)
    WHERE follow_step > 0;

-- Comentários
COMMENT ON COLUMN leads.follow_step IS 'Passo atual da cadência de follow-up (0-4). 0 = nenhum follow enviado.';
COMMENT ON COLUMN bookings.calcom_booking_uid IS 'UID público do booking no Cal.com (para reschedule/cancel via API).';
COMMENT ON COLUMN agent_snapshots.should_pause_ai IS 'Se a IA decidiu pausar nesta execução.';
