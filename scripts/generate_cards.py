import os
import json
import numpy as np
import qrcode
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL = "https://mtugbmwikuvfobykuvtl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10dWdibXdpa3V2Zm9ieWt1dnRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjIzMTQsImV4cCI6MjA3OTU5ODMxNH0.Z_cFuQxckxs5EHDfK2jhRtKLJ66IpTKb64PJeaUtDMA" 

# For now using localhost. Update after Vercel deployment
BASE_URL = "http://localhost:5173" 

NUM_CARDS = 150
OUTPUT_DIR = "qr_codes"

# --- SETUP ---
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Warning: Could not connect to Supabase. Check credentials. Error: {e}")
    supabase = None

def generate_tombola_card():
    """
    Generates a valid Tombola card (3x9 matrix).
    Rules:
    - 3 rows, 9 columns.
    - 5 numbers per row.
    - Columns represent decades:
      Col 0: 1-9
      Col 1: 10-19
      ...
      Col 8: 80-90
    """
    card = np.full((3, 9), 0, dtype=int)
    
    # 1. Generate numbers for each column to ensure coverage
    # We need 15 numbers total.
    # Each column must have at least 1 number (usually). 
    # But standard rules are strictly 5 numbers per row.
    
    # Let's use a simplified robust approach:
    # 1. Create a pool of numbers for each column.
    # 2. Fill the card satisfying the constraints.
    
    # Column ranges
    col_ranges = []
    for i in range(9):
        start = i * 10
        end = (i * 10) + 9
        if i == 0: start = 1
        if i == 8: end = 90
        col_ranges.append(list(range(start, end + 1)))

    while True:
        # Reset card
        card.fill(0)
        
        # Track numbers used to avoid duplicates across the whole card (though ranges handle this mostly)
        # Actually, we just need to pick distinct numbers for each column.
        
        # Strategy:
        # We need exactly 5 numbers per row.
        # Total 15 numbers.
        # Each column can have 0, 1, 2, or 3 numbers (usually max 2 or 3).
        # Standard Tombola rule: Every column must have at least one number? 
        # Actually, strict rules say: "In ogni cartella ci sono 15 numeri... 5 per riga...".
        # It's not strictly required that EVERY column has a number, but it's typical.
        # However, with 15 numbers and 9 columns, some columns will have more than 1.
        
        # Let's try a row-by-row generation with column constraints.
        
        # To simplify and ensure validity:
        # 1. Select 5 distinct column indices for Row 1.
        # 2. Select 5 distinct column indices for Row 2.
        # 3. Select 5 distinct column indices for Row 3.
        # Constraint: A column cannot have more than 3 numbers (obviously, only 3 rows).
        # Constraint: Ideally, distribute numbers so columns aren't empty too often, but 3x5=15, 9 cols. 
        # 6 cols will have at least 1, maybe some empty? No, usually all cols have at least one number in a SET of cards, but a single card might have empty cols?
        # Actually, a single card MUST have empty columns (4 per row are empty).
        
        # Let's randomly choose columns for each row.
        row_cols = []
        for _ in range(3):
            row_cols.append(np.random.choice(9, 5, replace=False))
            
        # Check column density
        col_counts = np.zeros(9, dtype=int)
        for rc in row_cols:
            for c in rc:
                col_counts[c] += 1
        
        # If any column has 3 numbers, it's allowed.
        # If any column is empty? It's allowed in a single card.
        # But let's try to be nice and ensure we don't have too many empty cols if possible, 
        # or just proceed. The strict rule is just 5 per row and correct decades.
        
        # Now fill with numbers
        used_numbers = set()
        valid_card = True
        
        for r_idx, cols in enumerate(row_cols):
            cols.sort() # Sort column indices so numbers appear in order
            for c_idx in cols:
                # Pick a number for this column
                possible = [n for n in col_ranges[c_idx] if n not in used_numbers]
                if not possible:
                    valid_card = False
                    break
                
                # We need to pick a number that is consistent with vertical ordering if we had multiple in col.
                # But here we are filling row by row. 
                # If we have multiple numbers in a column, they must be sorted vertically.
                # So we should pick ALL numbers for a column first, then assign to rows?
                pass
        
        if not valid_card:
            continue

        # BETTER STRATEGY:
        # 1. Decide how many numbers each column gets (total 15).
        #    Each col gets at least 1? 15 numbers / 9 cols = 1.6. 
        #    So 6 cols get 2, 3 cols get 1? Or some get 3?
        #    Let's stick to the row-first approach but fix the sorting later.
        
        # Let's use a library-like logic simplified:
        # Generate 15 numbers distributed across columns correctly?
        # No, the 5-per-row constraint is hard to satisfy if we just pick 15 numbers.
        
        # Let's go back to Row-First, but be careful.
        # Actually, simple rejection sampling works fast enough for N=10.
        
        # Draft 2:
        # 1. Generate structure (0s and 1s)
        structure = np.zeros((3, 9), dtype=int)
        
        # Ensure each column has at least 1 number? Not strictly required for a single card, 
        # but usually preferred. Let's relax that and just enforce 5 per row.
        
        # To ensure good distribution, let's force:
        # - Row 0: 5 random cols
        # - Row 1: 5 random cols
        # - Row 2: 5 random cols
        # Check if any column has > 3 (impossible) or if we want to avoid 0.
        # Let's just randomize until we are happy-ish.
        
        for r in range(3):
            cols = np.random.choice(9, 5, replace=False)
            structure[r, cols] = 1
            
        # Now fill with numbers
        # For each column, see how many numbers we need.
        for c in range(9):
            count = np.sum(structure[:, c])
            if count > 0:
                # Pick 'count' unique numbers from the range
                nums = np.random.choice(col_ranges[c], count, replace=False)
                nums.sort() # Ascending order top to bottom
                
                # Place them
                current_num_idx = 0
                for r in range(3):
                    if structure[r, c] == 1:
                        card[r, c] = nums[current_num_idx]
                        current_num_idx += 1
        
        # Check if we successfully created it (we always do with this logic)
        break
        
    # Convert to list for JSON serialization, replace 0 with None for cleaner frontend handling if desired,
    # or keep 0. The prompt said "0 o null". Let's keep 0 for int array, or convert to None.
    # Let's use None for empty to be explicit.
    card_list = card.tolist()
    for r in range(3):
        for c in range(9):
            if card_list[r][c] == 0:
                card_list[r][c] = None
                
    return card_list

def main():
    print(f"Generating {NUM_CARDS} cards...")
    
    for i in range(1, NUM_CARDS + 1):
        card_data = generate_tombola_card()
        
        # 1. Upload to Supabase
        card_id = i # Fallback if insert fails or we want to force ID (Supabase auto-increments usually)
        
        if supabase:
            try:
                # Insert and get the ID
                data = {"numbers": card_data}
                res = supabase.table("cards").insert(data).execute()
                # Assuming successful insert, get ID
                if res.data:
                    card_id = res.data[0]['id']
                    print(f"Card {i} inserted with DB ID: {card_id}")
            except Exception as e:
                print(f"Error inserting card {i}: {e}")
                # Continue generating QR locally even if DB fails, using loop index as ID
        
        # 2. Generate QR Code
        # URL format: BASE_URL?card_id=ID
        url = f"{BASE_URL}?card_id={card_id}"
        qr = qrcode.make(url)
        
        filename = f"{OUTPUT_DIR}/qr_card_{card_id}.png"
        qr.save(filename)
        print(f"Saved QR: {filename}")

if __name__ == "__main__":
    main()
