-- =====================================================================
-- V360 — tabela de usuários do app (login + permissões por unidade)
-- Rode isto no Supabase → SQL Editor.
-- =====================================================================
create table if not exists public.v360_usuarios (
  id          bigint generated always as identity primary key,
  email       text unique not null,
  senha_hash  text not null,                       -- sha256(pepper + senha)
  nome        text,
  role        text not null default 'gestor',      -- 'gestor' ou 'master'
  unidades    jsonb not null default '[]'::jsonb,  -- "*" (todas) ou ["PORTO VELHO - UNID 1", ...]
  ativo       boolean not null default true,
  criado_em   timestamptz not null default now()
);

-- O app (Streamlit) precisa LER e ESCREVER nesta tabela com a SUPABASE_KEY
-- dos Secrets. Duas formas de permitir:
--
-- A) RECOMENDADO: use a chave *service_role* no Secrets (SUPABASE_KEY).
--    Ela fica só no servidor do Streamlit (não vaza pro navegador) e já
--    tem acesso total — pode deixar a RLS ligada.
--
-- B) Se preferir manter a chave anon, desligue a RLS SÓ desta tabela
--    (uso interno). Descomente a linha abaixo:
-- alter table public.v360_usuarios disable row level security;

-- Observação: as senhas ficam com hash (nunca em texto). O master continua
-- vindo dos Secrets ([usuarios.alexandre]) — é o bootstrap e não some daqui.
