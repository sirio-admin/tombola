import json
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
CARDS_JSON_FILE = "all_cards.json"
BACKGROUND_IMAGE = "../cartella orizzonatale.jpeg"
OUTPUT_PDF = "cartelle_stampabili_201-350.pdf"
START_CARD = 201  # First card to include (1-indexed)
END_CARD = 350    # Last card to include (1-indexed)

# PDF Layout (A4 Landscape)
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)  # 842 x 595 points
CARDS_PER_ROW = 2
CARDS_PER_COL = 2
CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL  # 4 cards per page

# Gap between cards (in points, ~5mm = 15 points)
GAP = 15

# Card dimensions (reduced to account for gaps)
CARD_WIDTH = (PAGE_WIDTH - (GAP * (CARDS_PER_ROW + 1))) / CARDS_PER_ROW
CARD_HEIGHT = (PAGE_HEIGHT - (GAP * (CARDS_PER_COL + 1))) / CARDS_PER_COL

# Card grid configuration (matching frontend)
GRID_ROWS = 3
GRID_COLS = 7  # 7 columns format

def validate_card(card_data):
    """
    Validate that a card has exactly 15 numbers (5 per row).

    Args:
        card_data: Card data dict
    Returns:
        tuple: (is_valid, error_message)
    """
    numbers = card_data['numbers']
    card_num = card_data['card_number']

    if len(numbers) != 3:
        return False, f"Card #{card_num}: Wrong number of rows ({len(numbers)}, expected 3)"

    total_numbers = 0
    for row_idx, row in enumerate(numbers):
        if len(row) != 7:
            return False, f"Card #{card_num}: Row {row_idx+1} has {len(row)} columns (expected 7)"

        row_numbers = sum(1 for cell in row if cell is not None)
        total_numbers += row_numbers

        if row_numbers != 5:
            return False, f"Card #{card_num}: Row {row_idx+1} has {row_numbers} numbers (expected 5)"

    if total_numbers != 15:
        return False, f"Card #{card_num}: Total {total_numbers} numbers (expected 15)"

    return True, None

def load_cards():
    """Load cards from JSON file."""
    print(f"Loading cards from {CARDS_JSON_FILE}...")
    with open(CARDS_JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract cards 201-300 (indices 200-299 in array)
    all_cards = data['cards']
    selected_cards = all_cards[START_CARD-1:END_CARD]

    print(f"  [OK] Loaded {len(selected_cards)} cards (#{START_CARD}-#{END_CARD})")

    # Validate all cards
    print("\nValidating cards...")
    invalid_cards = []
    for card in selected_cards:
        is_valid, error = validate_card(card)
        if not is_valid:
            invalid_cards.append(error)

    if invalid_cards:
        print(f"  [ERROR] Found {len(invalid_cards)} invalid cards:")
        for error in invalid_cards:
            print(f"    - {error}")
        raise ValueError("Invalid cards detected. Cannot generate PDF.")

    print(f"  [OK] All {len(selected_cards)} cards validated successfully")
    print(f"       Each card has exactly 15 numbers (5 per row)")

    return selected_cards

def draw_card_on_pdf(c, card_data, x, y, width, height):
    """
    Draw a single tombola card on the PDF canvas.

    Args:
        c: ReportLab canvas
        card_data: Card data dict with 'card_number' and 'numbers'
        x, y: Bottom-left corner position
        width, height: Card dimensions
    """
    # Draw background image
    try:
        img = ImageReader(BACKGROUND_IMAGE)
        c.drawImage(img, x, y, width=width, height=height, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"  [WARNING] Could not load background image: {e}")
        # Draw fallback border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(2)
        c.rect(x, y, width, height)

    # Extract numbers matrix (3x9 but we only show first 7 columns)
    numbers = card_data['numbers']

    # Grid positioning (adjusted for landscape orientation with decorative border)
    # Optimized margins to fit within the yellow border (from test results)
    margin_x = width * 0.14  # 14% margin on sides
    margin_y = height * 0.34  # 34% margin on top/bottom

    grid_width = width - (2 * margin_x)
    grid_height = height - (2 * margin_y)

    cell_width = grid_width / GRID_COLS
    cell_height = grid_height / GRID_ROWS

    # Font settings (matching frontend - bold, black)
    c.setFillColorRGB(0, 0, 0)  # Black color
    font_size = min(cell_width, cell_height) * 0.45  # Slightly smaller to avoid overlap
    c.setFont("Helvetica-Bold", font_size)

    # Draw all cells (both empty and filled)
    for row_idx in range(GRID_ROWS):
        for col_idx in range(GRID_COLS):  # Only first 7 columns
            number = numbers[row_idx][col_idx]

            # Calculate cell center position
            cell_x = x + margin_x + (col_idx * cell_width) + (cell_width / 2)
            cell_y = y + height - margin_y - (row_idx * cell_height) - (cell_height / 2)

            # Draw cell background (without alpha for consistency)
            if number is not None:
                # Filled cell - white background
                c.setFillColorRGB(1, 1, 1)  # Pure white
                c.setStrokeColorRGB(0.75, 0.75, 0.75)  # Medium gray border
            else:
                # Empty cell - light gray background
                c.setFillColorRGB(0.93, 0.93, 0.93)  # Light gray (no transparency)
                c.setStrokeColorRGB(0.80, 0.80, 0.80)  # Slightly darker gray border

            c.setLineWidth(1)
            c.roundRect(
                cell_x - cell_width * 0.42,
                cell_y - cell_height * 0.42,
                cell_width * 0.84,
                cell_height * 0.84,
                cell_width * 0.08,  # Rounded corners
                fill=1,
                stroke=1
            )

            # Draw number if cell is filled
            if number is not None:
                c.setFillColorRGB(0, 0, 0)  # Black
                text_width = c.stringWidth(str(number), "Helvetica-Bold", font_size)
                text_x = cell_x - (text_width / 2)
                text_y = cell_y - (font_size / 3)  # Adjust for vertical centering

                c.drawString(text_x, text_y, str(number))

    # Optional: Draw card number at the bottom
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    card_num_text = f"Cartella #{card_data['card_number']}"
    text_width = c.stringWidth(card_num_text, "Helvetica-Bold", 10)
    c.drawString(x + (width - text_width) / 2, y + 5, card_num_text)

def generate_pdf():
    """Generate PDF with all cards."""
    print("=" * 60)
    print("TOMBOLA PDF GENERATOR")
    print("=" * 60)
    print(f"Cards range: #{START_CARD} to #{END_CARD}")
    print(f"Layout: {CARDS_PER_ROW}x{CARDS_PER_COL} cards per page")
    print(f"Output: {OUTPUT_PDF}")
    print("=" * 60)

    # Load cards
    cards = load_cards()

    if len(cards) == 0:
        print("[ERROR] No cards to process!")
        return

    # Create PDF
    print(f"\nGenerating PDF...")
    c = canvas.Canvas(OUTPUT_PDF, pagesize=landscape(A4))

    total_pages = (len(cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
    card_index = 0

    for page_num in range(total_pages):
        print(f"  [OK] Processing page {page_num + 1}/{total_pages}")

        # Draw cards on this page (2x2 grid)
        for row in range(CARDS_PER_COL):
            for col in range(CARDS_PER_ROW):
                if card_index >= len(cards):
                    break

                # Calculate position (with gaps)
                x = GAP + (col * (CARD_WIDTH + GAP))
                y = GAP + ((CARDS_PER_COL - 1 - row) * (CARD_HEIGHT + GAP))  # Flip Y axis

                # Draw card
                draw_card_on_pdf(
                    c,
                    cards[card_index],
                    x, y,
                    CARD_WIDTH,
                    CARD_HEIGHT
                )

                card_index += 1

        # New page if there are more cards
        if card_index < len(cards):
            c.showPage()

    # Save PDF
    c.save()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"[OK] Generated {total_pages} pages")
    print(f"[OK] Total cards: {len(cards)}")
    print(f"[OK] Saved to: {OUTPUT_PDF}")
    print("=" * 60)
    print("\nIl PDF è pronto per la stampa!")
    print(f"Contiene le cartelle #{START_CARD}-#{END_CARD} (100 cartelle totali)")
    print("4 cartelle per pagina in formato A4 landscape")

if __name__ == "__main__":
    try:
        generate_pdf()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
