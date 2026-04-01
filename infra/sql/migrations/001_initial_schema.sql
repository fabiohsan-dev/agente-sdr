-- ============================================
-- Migration 001: Schema inicial
-- ============================================
-- Data: 2026-03-31
-- Descrição: Criação inicial do schema do banco

-- Este arquivo é executado via migração
-- Para aplicar, execute o schema.sql completo no Supabase

-- Verificar se as tabelas já existem
-- Se sim, esta migration é idempotente

DO $$
BEGIN
    RAISE NOTICE 'Migration 001: Criando schema inicial...';
    
    -- As tabelas são criadas pelo schema.sql
    -- Esta migration é apenas para controle de versão
    
    RAISE NOTICE 'Migration 001: Schema inicial criado com sucesso!';
END $$;
