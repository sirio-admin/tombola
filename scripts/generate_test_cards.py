import os
import json
import numpy as np
import qrcode
from supabase import create_client, Client

# --- CONFIGURATION ---
SUPABASE_URL = "https://mtugbmwikuvfobykuvtl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10dWdibXdpa3V2Zm9ieWt1dnRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjIzMTQsImV4cCI6MjA3OTU5ODMxNH0.Z_cFuQxckxs5EHDfK2jhRtKLJ66IpTKb64PJeaUtDMA"

BASE_URL = "http://localhost:5173"
NUM_TEST_CARDS = 5  # Number of test cards to generate
OUTPUT_DIR = "qr_codes_test"

# --- SETUP ---
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Connected to Supabase")
except Exception as e:
    print(f"✗ Could not connect to Supabase: {e}")
    supabase = None

def generate_tombola_card():
    """
    Generates a valid Tombola card (3x9 matrix).
    """
    col_ranges = []
    for i in range(9):
        start = i * 10
        end = (i * 10) + 9
        if i == 0: start = 1
        if i == 8: end = 90
        col_ranges.append(list(range(start, end + 1)))

    structure = np.zeros((3, 9), dtype=int)

    for r in range(3):
        cols = np.random.choice(9, 5, replace=False)
        structure[r, cols] = 1

    card = np.zeros((3, 9), dtype=int)

    for c in range(9):
        count = np.sum(structure[:, c])
        if count > 0:
            nums = np.random.choice(col_ranges[c], count, replace=False)
            nums.sort()

            num_idx = 0
            for r in range(3):
                if structure[r, c] == 1:
                    card[r, c] = nums[num_idx]
                    num_idx += 1

    card_list = card.tolist()
    for r in range(3):
        for c in range(9):
            if card_list[r][c] == 0:
                card_list[r][c] = None

    return card_list

def main():
    print("=" * 60)
    print("TOMBOLA TEST CARD GENERATOR")
    print("=" * 60)
    print(f"Generating {NUM_TEST_CARDS} test cards...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)

    if not supabase:
        print("\n✗ Cannot proceed without Supabase connection")
        return

    card_ids = []

    for i in range(NUM_TEST_CARDS):
        card_data = generate_tombola_card()

        # Upload to Supabase
        try:
            data = {"numbers": card_data}
            res = supabase.table("cards").insert(data).execute()

            if res.data:
                card_id = res.data[0]['id']
                card_ids.append(card_id)
                print(f"✓ Card {i+1}: Uploaded with ID {card_id}")

                # Generate QR Code
                url = f"{BASE_URL}?card_id={card_id}"
                qr = qrcode.make(url)
                filename = f"{OUTPUT_DIR}/qr_card_{card_id}.png"
                qr.save(filename)
                print(f"  → QR saved: {filename}")
                print(f"  → URL: {url}")

            else:
                print(f"✗ Card {i+1}: Failed to upload")

        except Exception as e:
            print(f"✗ Card {i+1}: Error - {e}")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Generated {len(card_ids)} test cards")
    print(f"✓ QR codes saved in {OUTPUT_DIR}/")
    print("\nNext steps:")
    print(f"1. Start frontend: cd frontend && npm run dev")
    print(f"2. Open: {BASE_URL}")
    print(f"3. Test with URLs:")
    for card_id in card_ids:
        print(f"   - {BASE_URL}?card_id={card_id}")
    print("=" * 60)

if __name__ == "__main__":
    main()