-- FIX DEFINITIVO RLS POLICIES
-- Esegui questo script su Supabase SQL Editor per resettare e correggere tutte le policy

-- 1. Disabilita RLS temporaneamente per pulire
ALTER TABLE cards DISABLE ROW LEVEL SECURITY;

-- 2. Rimuovi TUTTE le policy esistenti per evitare conflitti
DROP POLICY IF EXISTS "Enable read access for all users" ON cards;
DROP POLICY IF EXISTS "Enable claim for unclaimed cards" ON cards;
DROP POLICY IF EXISTS "Enable update for card owners" ON cards;
DROP POLICY IF EXISTS "Enable insert for all users" ON cards;
DROP POLICY IF EXISTS "Enable update for claiming and marking" ON cards;
DROP POLICY IF EXISTS "Enable update for all" ON cards;

-- 3. Riabilita RLS
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;

-- 4. Ricrea le policy corrette

-- SELECT: Tutti possono leggere tutto
CREATE POLICY "Enable read access for all users" ON cards
    FOR SELECT
    USING (true);

-- INSERT: Tutti possono inserire (per lo script Python)
CREATE POLICY "Enable insert for all users" ON cards
    FOR INSERT
    WITH CHECK (true);

-- UPDATE: Tutti possono aggiornare
-- Nota: Poiché usiamo un UUID client-side (non Supabase Auth), 
-- non possiamo verificare l'identità lato server. 
-- Ci affidiamo alla logica del frontend (WHERE owner_uuid = ...) per la sicurezza.
CREATE POLICY "Enable update for all users" ON cards
    FOR UPDATE
    USING (true)
    WITH CHECK (true);
