import os
import json
import sys
import numpy as np
import qrcode
from supabase import create_client, Client

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- CONFIGURATION ---
SUPABASE_URL = "https://mtugbmwikuvfobykuvtl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10dWdibXdpa3V2Zm9ieWt1dnRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjIzMTQsImV4cCI6MjA3OTU5ODMxNH0.Z_cFuQxckxs5EHDfK2jhRtKLJ66IpTKb64PJeaUtDMA"

# Production URL from Vercel deployment (custom domain)
BASE_URL = "https://tombola-natale-sidea.vercel.app"

TOTAL_CARDS = 350  # Total cards to generate (200 for Supabase + 150 for PDF)
UPLOAD_CARDS = 200  # Number of cards to upload to Supabase
OUTPUT_DIR = "qr_codes"
CARDS_JSON_FILE = "all_cards.json"

# --- SETUP ---
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[OK] Connected to Supabase")
except Exception as e:
    print(f"[ERROR] Could not connect to Supabase: {e}")
    supabase = None

def generate_tombola_card():
    """
    Generates a valid Tombola card (3x7 matrix).
    Rules:
    - 3 rows, 7 columns.
    - 5 numbers per row, 2 empty cells per row.
    - Columns represent ranges covering 1-90:
      Col 0: 1-13
      Col 1: 14-26
      Col 2: 27-39
      Col 3: 40-52
      Col 4: 53-65
      Col 5: 66-78
      Col 6: 79-90
    - Numbers within each column are sorted ascending (top to bottom)
    """
    # Column ranges for 7 columns covering 1-90
    col_ranges = [
        list(range(1, 14)),    # Col 0: 1-13
        list(range(14, 27)),   # Col 1: 14-26
        list(range(27, 40)),   # Col 2: 27-39
        list(range(40, 53)),   # Col 3: 40-52
        list(range(53, 66)),   # Col 4: 53-65
        list(range(66, 79)),   # Col 5: 66-78
        list(range(79, 91))    # Col 6: 79-90
    ]

    # Create structure: determine which cells have numbers (1) and which are empty (0)
    structure = np.zeros((3, 7), dtype=int)

    # Each row must have exactly 5 numbers
    for r in range(3):
        cols = np.random.choice(7, 5, replace=False)
        structure[r, cols] = 1

    # Fill card with numbers
    card = np.zeros((3, 7), dtype=int)

    for c in range(7):
        count = np.sum(structure[:, c])
        if count > 0:
            # Pick 'count' unique numbers from this column's range
            nums = np.random.choice(col_ranges[c], count, replace=False)
            nums.sort()  # Sort ascending for vertical ordering

            # Place numbers in the column
            num_idx = 0
            for r in range(3):
                if structure[r, c] == 1:
                    card[r, c] = nums[num_idx]
                    num_idx += 1

    # Convert to list and replace 0 with None
    card_list = card.tolist()
    for r in range(3):
        for c in range(7):
            if card_list[r][c] == 0:
                card_list[r][c] = None

    return card_list

def validate_card_integrity(card):
    """
    Comprehensive validation of a Tombola card.
    Ensures the card follows ALL rules for 3x7 card format.

    Args:
        card: 3x7 matrix with numbers or None

    Returns:
        tuple: (is_valid, error_message)
    """
    # Check dimensions
    if len(card) != 3:
        return False, f"Invalid card structure: {len(card)} rows (expected 3)"

    for row_idx, row in enumerate(card):
        if len(row) != 7:
            return False, f"Row {row_idx} has {len(row)} columns (expected 7)"

    # Check numbers per row (exactly 5 per row)
    for row_idx, row in enumerate(card):
        non_none = [n for n in row if n is not None]
        if len(non_none) != 5:
            return False, f"Row {row_idx} has {len(non_none)} numbers (expected 5)"

    # Collect all numbers for further validation
    all_numbers = []
    for row in card:
        for num in row:
            if num is not None:
                all_numbers.append(num)

    # Check total numbers (must be 15)
    if len(all_numbers) != 15:
        return False, f"Card has {len(all_numbers)} numbers (expected 15)"

    # CRITICAL: Check no duplicate numbers on the same card
    if len(all_numbers) != len(set(all_numbers)):
        duplicates = [n for n in all_numbers if all_numbers.count(n) > 1]
        return False, f"Duplicate numbers found on card: {set(duplicates)}"

    # Check all numbers are in valid range (1-90)
    for num in all_numbers:
        if not (1 <= num <= 90):
            return False, f"Number {num} outside valid range (1-90)"

    # Check column ranges and vertical sorting
    # Define column ranges for 7 columns
    col_ranges_validation = [
        (1, 13), (14, 26), (27, 39), (40, 52), (53, 65), (66, 78), (79, 90)
    ]

    for col_idx in range(7):
        # Get column range
        col_min, col_max = col_ranges_validation[col_idx]

        # Collect column numbers
        col_numbers = []
        for row_idx in range(3):
            num = card[row_idx][col_idx]
            if num is not None:
                # Check range
                if not (col_min <= num <= col_max):
                    return False, f"Number {num} in column {col_idx} outside range [{col_min}-{col_max}]"
                col_numbers.append(num)

        # Check vertical sorting
        if col_numbers != sorted(col_numbers):
            return False, f"Column {col_idx} not sorted: {col_numbers}"

        # Check column density (max 3 numbers per column)
        if len(col_numbers) > 3:
            return False, f"Column {col_idx} has {len(col_numbers)} numbers (max 3)"

    return True, None

def card_to_string(card):
    """
    Convert card to a string representation for uniqueness checking.
    Uses the non-null numbers sorted to create a unique fingerprint.
    """
    numbers = []
    for row in card:
        for num in row:
            if num is not None:
                numbers.append(num)
    numbers.sort()
    return ",".join(map(str, numbers))

def generate_unique_cards(num_cards):
    """
    Generate a specified number of unique Tombola cards.
    Returns a list of unique cards.
    """
    unique_cards = []
    card_fingerprints = set()
    attempts = 0
    max_attempts = num_cards * 100  # Safety limit to avoid infinite loops

    print(f"\nGenerating {num_cards} unique cards...")

    validation_failures = 0

    while len(unique_cards) < num_cards and attempts < max_attempts:
        attempts += 1
        card = generate_tombola_card()

        # CRITICAL: Validate card integrity before accepting it
        is_valid, error = validate_card_integrity(card)
        if not is_valid:
            validation_failures += 1
            if validation_failures % 100 == 0:
                print(f"  [WARNING] {validation_failures} validation failures so far: {error}")
            continue

        fingerprint = card_to_string(card)

        if fingerprint not in card_fingerprints:
            card_fingerprints.add(fingerprint)
            unique_cards.append(card)

            if len(unique_cards) % 50 == 0:
                print(f"  [OK] Generated {len(unique_cards)}/{num_cards} unique cards (attempts: {attempts}, failures: {validation_failures})")

    if len(unique_cards) < num_cards:
        print(f"  [WARNING] Could only generate {len(unique_cards)} unique cards after {attempts} attempts")
    else:
        print(f"  [OK] Successfully generated {num_cards} unique cards in {attempts} attempts")
        print(f"       Validation failures: {validation_failures}")
        print(f"       All cards verified: no duplicates, correct structure, valid ranges")

    return unique_cards

def save_cards_to_json(cards, filename):
    """
    Save all cards to a JSON file for reference.
    """
    print(f"\nSaving all {len(cards)} cards to {filename}...")

    cards_data = {
        "total_cards": len(cards),
        "cards": [{"card_number": i+1, "numbers": card} for i, card in enumerate(cards)]
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(cards_data, f, indent=2, ensure_ascii=False)

    print(f"  [OK] Saved to {filename}")

def upload_cards_to_supabase(cards, num_to_upload):
    """
    Upload the first N cards to Supabase.
    Returns a list of card IDs from the database.
    """
    if not supabase:
        print("\n[ERROR] Cannot upload to Supabase: no connection")
        return list(range(1, num_to_upload + 1))

    print(f"\nUploading first {num_to_upload} cards to Supabase...")

    card_ids = []

    for i, card in enumerate(cards[:num_to_upload]):
        try:
            data = {"numbers": card}
            res = supabase.table("cards").insert(data).execute()

            if res.data:
                card_id = res.data[0]['id']
                card_ids.append(card_id)

                if (i + 1) % 50 == 0:
                    print(f"  [OK] Uploaded {i + 1}/{num_to_upload} cards")
            else:
                print(f"  [ERROR] Failed to upload card {i + 1}: No data returned")
                card_ids.append(None)

        except Exception as e:
            print(f"  [ERROR] Error uploading card {i + 1}: {e}")
            card_ids.append(None)

    successful_uploads = sum(1 for cid in card_ids if cid is not None)
    print(f"  [OK] Successfully uploaded {successful_uploads}/{num_to_upload} cards")

    return card_ids

def generate_qr_codes(card_ids):
    """
    Generate QR codes for the cards that were uploaded to Supabase.
    """
    print(f"\nGenerating QR codes for {len(card_ids)} cards...")

    successful_qrs = 0

    for i, card_id in enumerate(card_ids):
        if card_id is None:
            print(f"  [WARNING] Skipping QR for card {i + 1} (not uploaded)")
            continue

        try:
            url = f"{BASE_URL}?card_id={card_id}"
            qr = qrcode.make(url)

            filename = f"{OUTPUT_DIR}/qr_card_{card_id}.png"
            qr.save(filename)
            successful_qrs += 1

            if (i + 1) % 50 == 0:
                print(f"  [OK] Generated {successful_qrs} QR codes")

        except Exception as e:
            print(f"  [ERROR] Error generating QR for card {card_id}: {e}")

    print(f"  [OK] Successfully generated {successful_qrs} QR codes in {OUTPUT_DIR}/")

def main():
    print("=" * 60)
    print("TOMBOLA CARD GENERATOR")
    print("=" * 60)
    print(f"Total cards to generate: {TOTAL_CARDS}")
    print(f"Cards to upload to Supabase: {UPLOAD_CARDS}")
    print(f"Cards to keep local only: {TOTAL_CARDS - UPLOAD_CARDS}")
    print("=" * 60)

    # Step 1: Generate all unique cards
    all_cards = generate_unique_cards(TOTAL_CARDS)

    # Step 2: Save all cards to JSON
    save_cards_to_json(all_cards, CARDS_JSON_FILE)

    # Step 3: Upload first N cards to Supabase
    card_ids = upload_cards_to_supabase(all_cards, UPLOAD_CARDS)

    # Step 4: Generate QR codes for uploaded cards
    generate_qr_codes(card_ids)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"[OK] Generated {len(all_cards)} unique cards")
    print(f"[OK] Saved all cards to {CARDS_JSON_FILE}")
    print(f"[OK] Uploaded {sum(1 for cid in card_ids if cid is not None)} cards to Supabase")
    print(f"[OK] Generated {len([f for f in os.listdir(OUTPUT_DIR) if f.startswith('qr_card_')])} QR codes")
    print(f"\nRemaining {TOTAL_CARDS - UPLOAD_CARDS} cards are saved in {CARDS_JSON_FILE}")
    print("and can be uploaded later if needed.")
    print("=" * 60)

if __name__ == "__main__":
    main()