import sys
from supabase import create_client, Client

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
SUPABASE_URL = "https://mtugbmwikuvfobykuvtl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10dWdibXdpa3V2Zm9ieWt1dnRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjIzMTQsImV4cCI6MjA3OTU5ODMxNH0.Z_cFuQxckxs5EHDfK2jhRtKLJ66IpTKb64PJeaUtDMA"

def main():
    print("=" * 60)
    print("VERIFYING SUPABASE CARDS")
    print("=" * 60)

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Connected to Supabase\n")
    except Exception as e:
        print(f"[ERROR] Could not connect to Supabase: {e}")
        return

    try:
        # Get total count
        result = supabase.table("cards").select("id", count="exact").execute()
        total_count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"Total cards in database: {total_count}")

        # Get first 5 card IDs
        first_cards = supabase.table("cards").select("id").order("id").limit(5).execute()
        print(f"\nFirst 5 card IDs:")
        for card in first_cards.data:
            print(f"  - ID: {card['id']}")

        # Get last 5 card IDs
        last_cards = supabase.table("cards").select("id").order("id", desc=True).limit(5).execute()
        print(f"\nLast 5 card IDs:")
        for card in reversed(last_cards.data):
            print(f"  - ID: {card['id']}")

        # Check if IDs start from 1
        if first_cards.data and first_cards.data[0]['id'] == 1:
            print("\n[OK] ✓ IDs start from 1 (correct)")
        else:
            first_id = first_cards.data[0]['id'] if first_cards.data else "N/A"
            print(f"\n[WARNING] ✗ IDs start from {first_id} (expected 1)")

        # Get a sample card to verify structure
        sample_card = supabase.table("cards").select("*").limit(1).execute()
        if sample_card.data:
            card = sample_card.data[0]
            numbers = card['numbers']
            all_nums = [n for row in numbers for n in row if n is not None]

            print(f"\nSample card verification (ID {card['id']}):")
            print(f"  - Total numbers: {len(all_nums)}")
            print(f"  - Numbers: {sorted(all_nums)}")
            print(f"  - Unique numbers: {len(set(all_nums))}")
            print(f"  - Has duplicates: {'YES ✗' if len(all_nums) != len(set(all_nums)) else 'NO ✓'}")

            # Check rows
            for i, row in enumerate(numbers):
                row_nums = [n for n in row if n is not None]
                print(f"  - Row {i+1}: {len(row_nums)} numbers")

        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
