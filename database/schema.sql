-- Tombola Cards Table
-- This table stores all the Tombola cards with their numbers and ownership information

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    numbers JSONB NOT NULL,
    owner_uuid UUID DEFAULT NULL,
    marked_numbers JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups by owner_uuid
CREATE INDEX IF NOT EXISTS idx_cards_owner_uuid ON cards(owner_uuid);

-- Enable Row Level Security
ALTER TABLE cards ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read cards
CREATE POLICY "Enable read access for all users" ON cards
    FOR SELECT
    USING (true);

-- Policy: Users can claim unclaimed cards (set owner_uuid when it's NULL)
CREATE POLICY "Enable claim for unclaimed cards" ON cards
    FOR UPDATE
    USING (owner_uuid IS NULL)
    WITH CHECK (true);

-- Policy: Users can update their own cards (mark numbers)
CREATE POLICY "Enable update for card owners" ON cards
    FOR UPDATE
    USING (owner_uuid IS NOT NULL)
    WITH CHECK (true);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER update_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE cards IS 'Stores Tombola game cards with ownership and marking information';
COMMENT ON COLUMN cards.id IS 'Unique card identifier';
COMMENT ON COLUMN cards.numbers IS 'JSONB 3x9 matrix containing the card numbers (null for empty spaces)';
COMMENT ON COLUMN cards.owner_uuid IS 'UUID of the device that claimed this card';
COMMENT ON COLUMN cards.marked_numbers IS 'Array of numbers that have been marked by the user';
