import os
from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://mtugbmwikuvfobykuvtl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10dWdibXdpa3V2Zm9ieWt1dnRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjIzMTQsImV4cCI6MjA3OTU5ODMxNH0.Z_cFuQxckxs5EHDfK2jhRtKLJ66IpTKb64PJeaUtDMA"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_card(card_id):
    print(f"Checking card {card_id}...")
    try:
        response = supabase.table("cards").select("*").eq("id", card_id).execute()
        if response.data:
            card = response.data[0]
            print(f"Card found!")
            print(f"ID: {card['id']}")
            print(f"Owner UUID: {card['owner_uuid']}")
            print(f"Marked Numbers: {card['marked_numbers']}")
        else:
            print("Card NOT found.")
    except Exception as e:
        print(f"Error reading: {e}")

    print("\nResetting card to NULL...")
    try:
        # We need to use the fake_uuid to "own" it to be able to set it back to null if we use the "owner only" policy,
        # BUT our new policy is "Enable update for all users", so anyone can update anything.
        response = supabase.table("cards").update({"owner_uuid": None}).eq("id", card_id).execute()
        print(f"Reset result: {response}")
    except Exception as e:
        print(f"Error resetting: {e}")

if __name__ == "__main__":
    check_card(151)
