import json
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
CARDS_JSON_FILE = "all_cards.json"
BACKGROUND_IMAGE = "../cartella orizzonatale.jpeg"
OUTPUT_PDF = "test_layout.pdf"

# Test different margin configurations
MARGIN_CONFIGS = [
    {"name": "Config 1: 24%/28%", "margin_x": 0.24, "margin_y": 0.28},
    {"name": "Config 2: 14%/20%", "margin_x": 0.28, "margin_y": 0.32},
    {"name": "Config 3: 16%/22%", "margin_x": 0.14, "margin_y": 0.34},
    {"name": "Config 4: 18%/24%", "margin_x": 0.32, "margin_y": 0.36},

]

GRID_ROWS = 3
GRID_COLS = 7

def load_test_card():
    """Load first card for testing."""
    print(f"Loading test card from {CARDS_JSON_FILE}...")
    with open(CARDS_JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Use first card
    return data['cards'][0]

def draw_card_with_config(c, card_data, x, y, width, height, config):
    """Draw card with specific margin configuration."""

    # Draw background image
    try:
        img = ImageReader(BACKGROUND_IMAGE)
        c.drawImage(img, x, y, width=width, height=height, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"  [WARNING] Could not load background image: {e}")
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(2)
        c.rect(x, y, width, height)

    numbers = card_data['numbers']

    # Apply margins from config
    margin_x = width * config['margin_x']
    margin_y = height * config['margin_y']

    grid_width = width - (2 * margin_x)
    grid_height = height - (2 * margin_y)

    cell_width = grid_width / GRID_COLS
    cell_height = grid_height / GRID_ROWS

    # Font settings
    c.setFillColorRGB(0, 0, 0)
    font_size = min(cell_width, cell_height) * 0.45  # Slightly smaller to avoid overlap
    c.setFont("Helvetica-Bold", font_size)

    # Draw numbers
    for row_idx in range(GRID_ROWS):
        for col_idx in range(min(GRID_COLS, len(numbers[row_idx]))):
            number = numbers[row_idx][col_idx]

            if number is not None:
                # Calculate cell center
                cell_x = x + margin_x + (col_idx * cell_width) + (cell_width / 2)
                cell_y = y + height - margin_y - (row_idx * cell_height) - (cell_height / 2)

                # Draw cell background
                c.setFillColorRGB(1, 1, 1, alpha=0.88)
                c.setStrokeColorRGB(0.8, 0.8, 0.8)
                c.setLineWidth(1)
                c.roundRect(
                    cell_x - cell_width * 0.42,
                    cell_y - cell_height * 0.42,
                    cell_width * 0.84,
                    cell_height * 0.84,
                    cell_width * 0.08,
                    fill=1,
                    stroke=1
                )

                # Draw number
                c.setFillColorRGB(0, 0, 0)
                text_width = c.stringWidth(str(number), "Helvetica-Bold", font_size)
                text_x = cell_x - (text_width / 2)
                text_y = cell_y - (font_size / 3)

                c.drawString(text_x, text_y, str(number))

    # Draw config label
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.9, 0, 0)  # Red
    label_text = config['name']
    c.drawString(x + 10, y + height - 20, label_text)

    # Draw margin info
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0.7)  # Blue
    margin_text = f"X:{int(config['margin_x']*100)}% Y:{int(config['margin_y']*100)}%"
    c.drawString(x + 10, y + 10, margin_text)

def generate_test_pdf():
    """Generate test PDF with different configurations."""
    print("=" * 60)
    print("TOMBOLA PDF LAYOUT TESTER")
    print("=" * 60)
    print(f"Testing {len(MARGIN_CONFIGS)} different margin configurations")
    print(f"Output: {OUTPUT_PDF}")
    print("=" * 60)

    # Load test card
    test_card = load_test_card()
    print(f"\n[OK] Using card #{test_card['card_number']} for testing")

    # Create PDF (A4 Landscape, 2x2 layout like final PDF)
    c = canvas.Canvas(OUTPUT_PDF, pagesize=landscape(A4))
    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

    CARD_WIDTH = PAGE_WIDTH / 2
    CARD_HEIGHT = PAGE_HEIGHT / 2

    print("\nGenerating test layouts...")

    # Draw 4 configurations (2x2 grid)
    positions = [
        (0, CARD_HEIGHT),           # Top-left
        (CARD_WIDTH, CARD_HEIGHT),  # Top-right
        (0, 0),                     # Bottom-left
        (CARD_WIDTH, 0),            # Bottom-right
    ]

    for idx, (config, (x, y)) in enumerate(zip(MARGIN_CONFIGS, positions)):
        print(f"  [OK] Drawing {config['name']}")
        draw_card_with_config(c, test_card, x, y, CARD_WIDTH, CARD_HEIGHT, config)

    # Save PDF
    c.save()

    print("\n" + "=" * 60)
    print("TEST PDF GENERATED!")
    print("=" * 60)
    print(f"[OK] Saved to: {OUTPUT_PDF}")
    print("\nOra apri il PDF e guarda quale configurazione si allinea meglio")
    print("con il contorno giallo dell'immagine.")
    print("\nQuando trovi quella giusta, dimmi quale (Config 1, 2, 3 o 4)")
    print("e aggiornerò lo script principale con quei valori!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        generate_test_pdf()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
