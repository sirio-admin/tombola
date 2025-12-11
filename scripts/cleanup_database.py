import os
import sys
from supabase import create_client, Client

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- CONFIGURATION ---
SUPABASE_URL = "https://mtugbmwikuvfobykuvtl.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Read from environment variable

if not SUPABASE_KEY:
    print("[ERROR] SUPABASE_SERVICE_KEY environment variable not set.")
    print("Please set it before running this script.")
    sys.exit(1)

def reset_card_ownership(supabase_client: Client):
    """
    Sets the owner_uuid to NULL for all cards in the 'cards' table.
    """
    print("\n[WARNING] This will RESET OWNERSHIP for ALL cards (owner_uuid = NULL)!")
    response = input("Type 'RESET' to confirm: ")

    if response != "RESET":
        print("\n[CANCELLED] Reset ownership cancelled")
        return

    print("\nResetting ownership for all cards...")
    try:
        update_result = supabase_client.table("cards").update({"owner_uuid": None, "marked_numbers": []}).eq("owner_uuid", "neq.null").execute()
        
        # Count affected rows
        affected_rows = len(update_result.data)
        print(f"[OK] Successfully reset ownership for {affected_rows} cards.")
        print("[OK] All cards are now unassigned.")
    except Exception as e:
        print(f"[ERROR] Error during ownership reset: {e}")
        print("\nTip: You may need to run this SQL manually in Supabase dashboard:")
        print("      UPDATE cards SET owner_uuid = NULL, marked_numbers = '[]';")

def delete_all_cards(supabase_client: Client):
    """
    Deletes all cards from the database and resets the ID sequence.
    """
    print("\n[WARNING] This will DELETE ALL cards from the database!")
    response = input("Type 'DELETE' to confirm: ")

    if response != "DELETE":
        print("\n[CANCELLED] Deletion cancelled")
        return

    print("\nDeleting all cards...")
    try:
        delete_result = supabase_client.table("cards").delete().neq("id", 0).execute()
        # Count affected rows from delete operation not directly available in supabas-py, 
        # so we query count after.
        
        # Reset the ID sequence to start from 1
        print("Resetting ID sequence to 1...")
        try:
            supabase_client.rpc('execute_sql', {'query': 'ALTER SEQUENCE cards_id_seq RESTART WITH 1'}).execute()
            print("  [OK] ID sequence reset to 1")
        except Exception as seq_error:
            print(f"  [WARNING] Could not reset sequence via RPC: {seq_error}")
            print("  [INFO] You may need to run this SQL manually in Supabase dashboard:")
            print("         ALTER SEQUENCE cards_id_seq RESTART WITH 1;")

        # Verify deletion
        verify_result = supabase_client.table("cards").select("id", count="exact").execute()
        remaining = verify_result.count if hasattr(verify_result, 'count') else len(verify_result.data)

        if remaining == 0:
            print("[OK] Successfully deleted all cards.")
            print("[OK] Database is now clean.")
        else:
            print(f"[WARNING] {remaining} cards still remain.")

    except Exception as e:
        print(f"[ERROR] Error during cleanup: {e}")
        print("\nTip: You may need to run this SQL manually in Supabase dashboard:")
        print("      DELETE FROM cards;")


def main():
    print("=" * 60)
    print("SUPABASE DATABASE MANAGEMENT")
    print("=" * 60)

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Connected to Supabase")
    except Exception as e:
        print(f"[ERROR] Could not connect to Supabase: {e}")
        return

    while True:
        print("\nChoose an action:")
        print("1. Reset all card ownership (set owner_uuid to NULL, clear marked_numbers)")
        print("2. DELETE ALL cards from database (and reset ID sequence)")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            reset_card_ownership(supabase)
        elif choice == '2':
            delete_all_cards(supabase)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()