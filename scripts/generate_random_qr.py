import sys
import qrcode

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Production URL from Vercel deployment (custom domain)
BASE_URL = "https://tombola-rdgbrz9f0-francescos-projects-db7529a0.vercel.app"

def generate_random_qr():
    """
    Generate a single QR code that automatically assigns a random available card.
    """
    print("=" * 60)
    print("TOMBOLA RANDOM QR CODE GENERATOR")
    print("=" * 60)

    # URL with random parameter
    url = f"{BASE_URL}?random=true"

    print(f"URL: {url}")
    print("\nGenerating QR code...")

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code
    filename = "qr_random_card.png"
    img.save(filename)

    print(f"[OK] QR code saved: {filename}")
    print("\n" + "=" * 60)
    print("INSTRUCTIONS")
    print("=" * 60)
    print("1. Print this QR code")
    print("2. When someone scans it, they will be automatically assigned")
    print("   the first available card from the database")
    print("3. The same person can scan multiple times and will get their")
    print("   original card (device UUID is saved in localStorage)")
    print("4. Different people will get different cards automatically")
    print("=" * 60)

if __name__ == "__main__":
    generate_random_qr()
