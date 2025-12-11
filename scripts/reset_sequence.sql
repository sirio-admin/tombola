-- SQL Script to reset the cards table sequence to 1
-- Run this in Supabase Dashboard -> SQL Editor

-- Step 1: Delete all cards
DELETE FROM cards;

-- Step 2: Reset the sequence to start from 1
ALTER SEQUENCE cards_id_seq RESTART WITH 1;

-- Step 3: Verify the sequence has been reset
SELECT nextval('cards_id_seq');  -- This should return 1

-- Step 4: Reset the sequence back (because we consumed 1 in step 3)
ALTER SEQUENCE cards_id_seq RESTART WITH 1;

-- Done! The next inserted card will have ID = 1
