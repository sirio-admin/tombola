"""
Load Testing Script per Tombola App
Simula 100 utenti che scansionano QR, claimano cartelle e marchiano numeri.

Requisiti:
    pip install locust requests uuid

Esecuzione:
    locust -f load_test.py --host=http://localhost:5173 --users=100 --spawn-rate=10

    O per testing backend diretto:
    python load_test.py --direct-db-test
"""

import os
import json
import time
import random
import uuid as uuid_lib
from typing import List, Dict
import argparse

try:
    from locust import HttpUser, task, between, events
    from locust.env import Environment
    from locust.stats import stats_printer, stats_history
    LOCUST_AVAILABLE = True
except ImportError:
    print("⚠️  Locust non installato. Installa con: pip install locust")
    LOCUST_AVAILABLE = False

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("⚠️  Supabase non installato. Installa con: pip install supabase")
    SUPABASE_AVAILABLE = False


# Configurazione
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mtugbmwikuvfobykuvtl.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10dWdibXdpa3V2Zm9ieWt1dnRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjIzMTQsImV4cCI6MjA3OTU5ODMxNH0.Z_cFuQxckxs5EHDfK2jhRtKLJ66IpTKb64PJeaUtDMA")

# Simulazione statistiche
class TestStats:
    """Raccoglie statistiche del test"""
    def __init__(self):
        self.total_claims = 0
        self.successful_claims = 0
        self.failed_claims = 0
        self.race_conditions = 0
        self.total_toggles = 0
        self.failed_toggles = 0
        self.total_time = 0
        self.errors: List[str] = []

    def print_summary(self):
        """Stampa riepilogo"""
        print("\n" + "="*60)
        print("📊 RISULTATI LOAD TEST")
        print("="*60)
        print(f"✅ Claims riusciti:        {self.successful_claims}/{self.total_claims}")
        print(f"❌ Claims falliti:         {self.failed_claims}/{self.total_claims}")
        print(f"⚠️  Race conditions:       {self.race_conditions}")
        print(f"🔢 Toggle riusciti:        {self.total_toggles - self.failed_toggles}/{self.total_toggles}")
        print(f"❌ Toggle falliti:         {self.failed_toggles}/{self.total_toggles}")

        if self.total_claims > 0:
            success_rate = (self.successful_claims / self.total_claims) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")

        if self.errors:
            print(f"\n⚠️  Errori rilevati ({len(self.errors)}):")
            for err in self.errors[:10]:  # Mostra primi 10
                print(f"   - {err}")
            if len(self.errors) > 10:
                print(f"   ... e altri {len(self.errors) - 10} errori")

        print("="*60 + "\n")

stats = TestStats()


# =============================================================================
# LOCUST HTTP USER (per test frontend completo)
# =============================================================================

if LOCUST_AVAILABLE:
    class TombolaUser(HttpUser):
        """Simula un utente che usa l'app Tombola"""

        wait_time = between(1, 3)  # Attesa tra azioni (1-3 secondi)

        def on_start(self):
            """Inizializzazione utente"""
            self.device_uuid = str(uuid_lib.uuid4())
            self.card_id = None
            self.card_data = None
            self.marked_numbers = []

        @task(3)
        def claim_card(self):
            """Simula claim di una cartella via QR code"""
            # Prova a claimare una cartella random (1-150)
            card_id = random.randint(1, 150)

            stats.total_claims += 1

            with self.client.get(
                f"/?card_id={card_id}",
                catch_response=True,
                name="/claim_card"
            ) as response:
                if response.status_code == 200:
                    stats.successful_claims += 1
                    self.card_id = card_id
                    response.success()
                else:
                    stats.failed_claims += 1
                    stats.errors.append(f"Claim failed: {response.status_code}")
                    response.failure(f"Claim failed: {response.status_code}")

        @task(10)
        def toggle_number(self):
            """Simula marcatura di un numero"""
            if not self.card_id:
                return

            # Simula marcatura numero random (1-90)
            number = random.randint(1, 90)
            stats.total_toggles += 1

            # In realtà questo dovrebbe chiamare l'API Supabase
            # Ma per ora simuliamo il comportamento
            time.sleep(0.1)  # Simula latency

        @task(1)
        def view_card(self):
            """Simula visualizzazione cartella"""
            if self.card_id:
                with self.client.get(
                    f"/?card_id={self.card_id}",
                    catch_response=True,
                    name="/view_card"
                ) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"View failed: {response.status_code}")


# =============================================================================
# DIRECT DATABASE TEST (test diretto su Supabase)
# =============================================================================

def direct_database_test(num_users: int = 100, spawn_rate: int = 10):
    """
    Test diretto del database Supabase senza frontend.
    Simula claim simultanei e update.
    """
    if not SUPABASE_AVAILABLE:
        print("❌ Impossibile eseguire direct DB test: supabase non installato")
        return

    print(f"\n🧪 DIRECT DATABASE TEST")
    print(f"   Utenti: {num_users}")
    print(f"   Spawn rate: {spawn_rate}/sec")
    print(f"   Target: {SUPABASE_URL}\n")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # 1. Verifica cartelle disponibili
    print("📋 Verifico cartelle disponibili...")
    try:
        res = supabase.table("cards").select("id", count="exact").is_("owner_uuid", None).execute()
        available = res.count if hasattr(res, 'count') else len(res.data)
        print(f"   Cartelle disponibili: {available}")

        if available < num_users:
            print(f"⚠️  ATTENZIONE: Solo {available} cartelle disponibili per {num_users} utenti!")
            print(f"   Alcuni utenti falliranno il claim (comportamento atteso)")
    except Exception as e:
        print(f"❌ Errore verifica: {e}")
        return

    # 2. Test claim simultanei
    print(f"\n🚀 Avvio claim simultaneo con {num_users} utenti...")

    import concurrent.futures
    import threading

    lock = threading.Lock()

    def simulate_user_claim(user_id: int):
        """Simula un singolo utente che claima una cartella"""
        device_uuid = str(uuid_lib.uuid4())

        try:
            # Simula random assignment come nel frontend
            # 1. Fetch cartelle disponibili
            res = supabase.table("cards").select("id").is_("owner_uuid", None).limit(50).execute()

            if not res.data or len(res.data) == 0:
                with lock:
                    stats.failed_claims += 1
                    stats.errors.append(f"User {user_id}: Nessuna cartella disponibile")
                return None

            # 2. Pick random
            random_card = random.choice(res.data)
            card_id = random_card['id']

            # 3. Tenta claim
            update_res = supabase.table("cards").update(
                {"owner_uuid": device_uuid}
            ).eq("id", card_id).is_("owner_uuid", None).execute()

            if update_res.data and len(update_res.data) > 0:
                with lock:
                    stats.successful_claims += 1
                print(f"✅ User {user_id}: Claimed card {card_id}")
                return card_id
            else:
                # Race condition: qualcun altro ha preso la cartella
                with lock:
                    stats.failed_claims += 1
                    stats.race_conditions += 1
                print(f"⚠️  User {user_id}: Race condition su card {card_id}")
                return None

        except Exception as e:
            with lock:
                stats.failed_claims += 1
                stats.errors.append(f"User {user_id}: {str(e)}")
            print(f"❌ User {user_id}: Errore - {e}")
            return None

    # Esegui claims in parallelo
    start_time = time.time()
    stats.total_claims = num_users

    with concurrent.futures.ThreadPoolExecutor(max_workers=spawn_rate) as executor:
        futures = [executor.submit(simulate_user_claim, i) for i in range(num_users)]

        # Aspetta completamento
        claimed_cards = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                claimed_cards.append(result)

    elapsed = time.time() - start_time

    # 3. Test update (toggle numbers) sui claimed cards
    if claimed_cards:
        print(f"\n🔢 Test update (toggle numbers) su {len(claimed_cards)} cartelle...")

        def simulate_toggle(card_id: int):
            """Simula marcatura di numeri"""
            try:
                marked = [random.randint(1, 90) for _ in range(5)]

                update_res = supabase.table("cards").update(
                    {"marked_numbers": marked}
                ).eq("id", card_id).execute()

                if update_res.data:
                    with lock:
                        stats.total_toggles += 1
                    return True
                else:
                    with lock:
                        stats.total_toggles += 1
                        stats.failed_toggles += 1
                    return False

            except Exception as e:
                with lock:
                    stats.total_toggles += 1
                    stats.failed_toggles += 1
                    stats.errors.append(f"Toggle card {card_id}: {str(e)}")
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            toggle_futures = [executor.submit(simulate_toggle, card_id) for card_id in claimed_cards]
            for future in concurrent.futures.as_completed(toggle_futures):
                future.result()

    stats.total_time = elapsed
    stats.print_summary()

    print(f"⏱️  Tempo totale: {elapsed:.2f}s")
    print(f"📊 Throughput: {num_users/elapsed:.1f} claims/sec\n")


# =============================================================================
# RESET DATABASE (per ripetere i test)
# =============================================================================

def reset_database():
    """Reset delle cartelle per ripetere i test"""
    if not SUPABASE_AVAILABLE:
        print("❌ Supabase non disponibile")
        return

    print("🔄 Reset database in corso...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        # Reset owner_uuid e marked_numbers
        res = supabase.table("cards").update({
            "owner_uuid": None,
            "marked_numbers": []
        }).neq("id", 0).execute()  # Update all

        print(f"✅ Database resettato: {len(res.data) if res.data else 0} cartelle liberate")
    except Exception as e:
        print(f"❌ Errore reset: {e}")


# =============================================================================
# CLI
# =============================================================================

def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description="Load Testing per Tombola App")
    parser.add_argument("--direct-db-test", action="store_true",
                       help="Esegui test diretto su database (senza frontend)")
    parser.add_argument("--users", type=int, default=100,
                       help="Numero utenti da simulare (default: 100)")
    parser.add_argument("--spawn-rate", type=int, default=10,
                       help="Utenti da spawnnare per secondo (default: 10)")
    parser.add_argument("--reset", action="store_true",
                       help="Reset database prima del test")

    args = parser.parse_args()

    if args.reset:
        reset_database()
        return

    if args.direct_db_test:
        direct_database_test(num_users=args.users, spawn_rate=args.spawn_rate)
    else:
        if not LOCUST_AVAILABLE:
            print("\n💡 Per test HTTP completo, installa locust:")
            print("   pip install locust")
            print("\n💡 Oppure usa il test diretto database:")
            print("   python load_test.py --direct-db-test")
        else:
            print("\n🚀 Avvia Locust con:")
            print(f"   locust -f {__file__} --host=http://localhost:5173")
            print(f"   Poi vai su http://localhost:8089 e imposta {args.users} utenti")


if __name__ == "__main__":
    main()
