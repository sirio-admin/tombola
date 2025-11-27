# Quick Start Guide - Tombola App 🚀

## Setup Veloce (5 minuti)

### 1️⃣ Database Supabase
```bash
# Vai su https://supabase.com/dashboard
# SQL Editor → Incolla il contenuto di database/schema.sql → Run
```

### 2️⃣ Test Locale Frontend (Opzionale)
```bash
cd frontend
npm run dev
# Apri http://localhost:5173?card_id=1
```

### 3️⃣ Deploy su Vercel
```bash
cd frontend
vercel

# Environment Variables su Vercel:
# VITE_SUPABASE_URL=https://mtugbmwikuvfobykuvtl.supabase.co
# VITE_SUPABASE_ANON_KEY=eyJhbGci... (dal file .env)
```

### 4️⃣ Genera Cartelle e QR
```bash
cd scripts
pip install -r requirements.txt

# IMPORTANTE: Modifica BASE_URL in generate_cards.py
# BASE_URL = "https://TUO-SITO.vercel.app"

python generate_cards.py
# Output: 50 cartelle + QR in qr_codes/
```

### 5️⃣ Stampa e Gioca!
```bash
# Stampa i file in scripts/qr_codes/
# Distribuisci ai giocatori
# Inizia il gioco! 🎉
```

## Comandi Utili

### Frontend
```bash
cd frontend
npm run dev      # Development server
npm run build    # Build production
npm run preview  # Preview build
```

### Python Script
```bash
cd scripts
python generate_cards.py    # Genera cartelle e QR
```

### Vercel Deployment
```bash
cd frontend
vercel           # Deploy preview
vercel --prod    # Deploy production
```

## Troubleshooting

### Frontend non si connette a Supabase
✓ Verifica `.env` in frontend/
✓ Controlla che le variabili inizino con `VITE_`

### Script Python dà errore
✓ Verifica `.env` in scripts/
✓ Assicurati di aver eseguito `pip install -r requirements.txt`

### QR code hanno URL sbagliato
✓ Aggiorna `BASE_URL` in `generate_cards.py`
✓ Rigenera i QR dopo il deploy

### Cartella "già presa"
✓ Comportamento corretto! Ogni cartella è univoca
✓ Per testare, pulisci localStorage del browser

## File Importanti

| File | Scopo |
|------|-------|
| `database/schema.sql` | Schema database da eseguire su Supabase |
| `scripts/generate_cards.py` | Genera cartelle e QR code |
| `scripts/.env` | Credenziali Supabase (backend) |
| `frontend/.env` | Credenziali Supabase (frontend) |
| `frontend/src/components/Card.jsx` | Componente principale |
| `frontend/public/assets/cartella-bg.png` | Immagine background (da personalizzare!) |

## Personalizzazioni Rapide

### Cambiare numero cartelle
In `scripts/generate_cards.py`:
```python
NUM_CARDS = 100  # Cambia qui
```

### Cambiare colori UI
In `frontend/src/components/Card.jsx`:
```jsx
// Background
className="bg-gradient-to-br from-slate-900 via-purple-900..."
// Cambia purple con: blue, red, green, etc.
```

### Usare la tua immagine
1. Esporta da Figma come PNG
2. Salva in `frontend/public/assets/cartella-bg.png`
3. Rebuild: `npm run build`

---

**Per la documentazione completa, leggi il [README.md](file:///Users/alessandropiccolo/tombola/README.md)**
