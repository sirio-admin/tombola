# Tombola Web Application 🎲

Una web app mobile-first per giocare a Tombola italiana con QR code, sviluppata con React, Python e Supabase.

## 📋 Panoramica

Questo progetto permette di:
1. Generare cartelle della Tombola valide
2. Creare QR code univoci per ogni cartella
3. Permettere agli utenti di "rivendicare" una cartella scansionando il QR code
4. Segnare i numeri durante il gioco

## 🏗️ Struttura del Progetto

```
tombola/
├── database/
│   └── schema.sql          # Schema Supabase
├── scripts/
│   ├── generate_cards.py   # Script Python per generare cartelle e QR
│   ├── requirements.txt    # Dipendenze Python
│   ├── .env               # Credenziali Supabase (non committare!)
│   ├── .env.example       # Template per .env
│   └── qr_codes/          # QR code generati (creata automaticamente)
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── Card.jsx   # Componente principale della cartella
    │   ├── lib/
    │   │   └── supabaseClient.js
    │   ├── App.jsx
    │   └── index.css
    ├── public/
    │   └── assets/
    │       └── cartella-bg.png  # AGGIUNGI LA TUA IMMAGINE QUI
    └── .env               # Credenziali Supabase frontend
```

## 🚀 Setup Iniziale

### 1. Configurazione Database Supabase

1. Vai su [Supabase](https://supabase.com) e apri il tuo progetto
2. Naviga a **SQL Editor**
3. Copia e incolla il contenuto di `database/schema.sql`
4. Esegui lo script per creare la tabella `cards` e le policy RLS

### 2. Configurazione Script Python

```bash
cd scripts

# Installa le dipendenze
pip install -r requirements.txt

# Le credenziali sono già configurate in .env
# Verifica che siano corrette
```

### 3. Configurazione Frontend React

```bash
cd frontend

# Le dipendenze sono già installate
# Verifica il file .env con le credenziali Supabase
```

### 4. Aggiungi l'Immagine della Cartella

**IMPORTANTE**: Devi aggiungere la tua immagine personalizzata della cartella:

1. Crea la tua immagine in Figma (o altro tool)
2. Esportala come PNG
3. Salvala in `frontend/public/assets/cartella-bg.png`
4. Potrebbe essere necessario aggiustare il CSS nel componente `Card.jsx` per allineare la griglia di numeri con l'immagine

## 🎮 Generazione Cartelle e QR Code

### Primo Test (Opzionale)

Prima di deployare, puoi testare lo script:

```bash
cd scripts
python generate_cards.py
```

Questo genererà:
- 50 cartelle nel database Supabase
- 50 QR code nella cartella `qr_codes/`
- I QR code punteranno a `https://YOUR-VERCEL-URL.vercel.app?card_id={id}`

**NOTA**: I QR code generati ora avranno un URL placeholder. Dovrai rigenerarli dopo il deploy.

### Dopo il Deploy su Vercel

1. Deploya il frontend su Vercel:
```bash
cd frontend
npm run build
# Segui le istruzioni di Vercel per il deploy
```

2. Una volta ottenuto l'URL di produzione (es. `https://tombola-natale.vercel.app`), aggiorna lo script Python:

```python
# In scripts/generate_cards.py, cambia:
BASE_URL = "https://tombola-natale.vercel.app"  # Il tuo URL Vercel
```

3. **IMPORTANTE**: Prima di rigenerare i QR code, elimina le cartelle esistenti dal database (o genera nuove cartelle con nuovi ID):

```bash
cd scripts
python generate_cards.py
```

4. Stampa i QR code dalla cartella `scripts/qr_codes/`

## 🎯 Come Funziona

### Flusso Utente

1. **L'organizzatore** stampa i QR code fisici
2. **L'utente** scansiona un QR code con lo smartphone
3. Il browser si apre automaticamente con l'URL: `https://tuo-sito.com?card_id=5`
4. L'app:
   - Controlla se esiste un UUID del dispositivo nel localStorage
   - Se non esiste, ne crea uno nuovo
   - Verifica lo stato della cartella nel database:
     - **Se libera** (`owner_uuid = NULL`): La assegna all'utente
     - **Se già sua**: Carica i numeri segnati
     - **Se di qualcun altro**: Mostra errore
5. L'utente può cliccare sui numeri per segnarli

### Logica del Database

```sql
-- Una cartella può essere:
owner_uuid = NULL          → Libera (nessuno l'ha rivendicata)
owner_uuid = 'abc-123...'  → Assegnata a un dispositivo specifico

-- I numeri segnati sono salvati in tempo reale
marked_numbers = [5, 12, 23, 48, 67]
```

## 🔧 Development

### Eseguire il Frontend in Sviluppo

```bash
cd frontend
npm run dev
```

L'app sarà disponibile su `http://localhost:5173`

Per testare:
- Apri `http://localhost:5173?card_id=1`
- Dovrebbe caricare la cartella #1 (se esiste nel database)

### Build per Produzione

```bash
cd frontend
npm run build
```

## 📝 Personalizzazione

### Modificare il Numero di Cartelle Generate

In `scripts/generate_cards.py`:

```python
NUM_CARDS = 100  # Cambia questo numero
```

### Personalizzare lo Stile della Cartella

Modifica `frontend/src/components/Card.jsx`:

- **Colori**: Cerca le classi Tailwind (es. `from-purple-900`, `to-slate-900`)
- **Griglia**: Modifica `gap-2`, padding, o dimensioni delle celle
- **Animazioni**: Aggiungi o modifica le classi `transition-all`, `hover:scale-105`, ecc.

### Allineamento Griglia con Immagine Background

Se i numeri non si allineano perfettamente con la tua immagine:

1. Apri `frontend/src/components/Card.jsx`
2. Cerca la sezione "Number Grid Overlay":
```jsx
<div className="absolute inset-0 p-4">
  <div className="grid grid-rows-3 gap-2 h-full">
```
3. Modifica:
   - `p-4` → padding generale
   - `gap-2` → spazio tra le celle
   - Aggiungi margini specifici per riga/colonna se necessario

## 🐛 Troubleshooting

### "Cartella non trovata"
- Verifica che lo script Python sia stato eseguito correttamente
- Controlla che il `card_id` nell'URL esista nel database

### "Cartella già presa"
- Questa è la logica corretta: ogni cartella può essere rivendicata da un solo dispositivo
- Per testare, pulisci il localStorage o usa un altro browser

### I numeri non si allineano con l'immagine
- Assicurati che l'immagine sia in `public/assets/cartella-bg.png`
- Regola il padding e il gap nella griglia CSS
- Controlla che l'aspect ratio dell'immagine sia corretto

### Errori di connessione a Supabase
- Verifica che le credenziali in `.env` siano corrette
- Controlla che le RLS policies siano state create correttamente
- Verifica che la tabella `cards` esista

## 📚 Tecnologie Utilizzate

- **Frontend**: React 18, Vite, Tailwind CSS
- **Backend**: Supabase (PostgreSQL)
- **Scripting**: Python 3, NumPy, QRCode
- **Autenticazione**: UUID nel localStorage (no auth complessa)

## 🎨 Prossimi Passi

1. ✅ Crea il database su Supabase
2. ✅ Genera le prime cartelle di test
3. ⚠️ **Aggiungi la tua immagine** in `frontend/public/assets/cartella-bg.png`
4. 🔄 Testa in locale
5. 🚀 Deploya su Vercel
6. 🔄 Rigenera i QR code con l'URL di produzione
7. 🖨️ Stampa i QR code

## 📄 Licenza

Progetto personale - Usa come preferisci!

---

**Buon divertimento con la Tombola! 🎉**
