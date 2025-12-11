import json

def get_card_numbers(card_data):
    """
    Extracts the 15 non-null numbers from a card's data and returns them as a sorted tuple.
    """
    numbers = []
    for row in card_data["numbers"]:
        for num in row:
            if num is not None:
                numbers.append(num)
    if len(numbers) != 15:
        print(f"Warning: Card {card_data.get('card_number', 'N/A')} has {len(numbers)} numbers instead of 15.")
    return tuple(sorted(numbers))

def verify_card_uniqueness(json_file_path):
    """
    Loads card data from a JSON file and checks for duplicate sets of 15 numbers.
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cards = data.get("cards", [])
    seen_card_sets = {} # Stores { (sorted_numbers_tuple): [card_numbers_list] }
    
    duplicates_found = False
    
    print(f"Verifying uniqueness for {len(cards)} cards from {json_file_path}...")

    for card in cards:
        card_number = card.get("card_number")
        card_set = get_card_numbers(card)

        if card_set in seen_card_sets:
            duplicates_found = True
            print(f"DUPLICATE FOUND!")
            print(f"  Card {card_number} ({card_set}) is a duplicate of cards: {seen_card_sets[card_set]}")
            seen_card_sets[card_set].append(card_number) # Add current card to list of duplicates
        else:
            seen_card_sets[card_set] = [card_number]

    if not duplicates_found:
        print("\nSUCCESS: No duplicate cards (same 15 numbers) found.")
    else:
        print("\nERROR: Duplicates found! Please review the output above.")
        
    # Also check if total_cards matches actual count
    actual_card_count = len(cards)
    declared_total_cards = data.get("total_cards")
    if declared_total_cards is not None and actual_card_count != declared_total_cards:
        print(f"WARNING: Declared total_cards ({declared_total_cards}) does not match actual card count ({actual_card_count}).")

if __name__ == "__main__":
    verify_card_uniqueness('scripts/all_cards.json')
