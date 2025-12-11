# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a mobile-first Italian Tombola (Bingo) web application that uses QR codes to distribute game cards. Players scan QR codes to claim unique cards, which are then tied to their device via localStorage UUID. The project consists of three main components:

1. **Python Card Generator** (`scripts/`) - Generates valid Tombola cards and QR codes
2. **React Frontend** (`frontend/`) - Mobile-first web app for playing
3. **Supabase Database** (`database/`) - PostgreSQL backend with RLS policies

## Development Commands

### Frontend Development
```bash
cd frontend
npm run dev      # Start dev server at http://localhost:5173
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Python Card Generation
```bash
cd scripts
pip install -r requirements.txt   # Install dependencies (numpy, qrcode[pil], supabase)
python generate_cards.py          # Generate cards and QR codes
python debug_card.py              # Debug/test individual cards
```

### Testing Frontend with Cards
Access a specific card in development: `http://localhost:5173?card_id=1`

## Architecture

### Card Claiming Flow
1. User scans QR code → Opens URL with `?card_id=X`
2. Frontend checks localStorage for `device_uuid` (creates one if missing)
3. Frontend fetches card from Supabase by ID
4. If `owner_uuid` is NULL → Claims card by setting `owner_uuid` to device UUID
5. If `owner_uuid` matches device UUID → Loads saved `marked_numbers`
6. If `owner_uuid` is different → Shows error (card already claimed)

### Database Schema (`cards` table)
- `id` - Card identifier (used in QR codes)
- `numbers` - JSONB 3x9 matrix of card numbers (null for empty cells)
- `owner_uuid` - UUID of claiming device (NULL = unclaimed)
- `marked_numbers` - JSONB array of numbers marked by user
- RLS policies allow: anyone to read, claim unclaimed cards, update owned cards

### Card Generation Algorithm
The Python script generates valid Tombola cards following Italian rules:
- 3 rows × 9 columns grid
- 5 numbers per row, 4 empty cells per row
- Columns represent decades: col 0 = 1-9, col 1 = 10-19, ..., col 8 = 80-90
- Numbers within columns are sorted ascending
- Each card has 15 unique numbers total

## Environment Setup

### Required `.env` Files

**`scripts/.env`** (Python backend):
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

**`frontend/.env`** (React frontend):
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Note: Frontend env vars MUST be prefixed with `VITE_` to be accessible in Vite.

### Database Setup
1. Create Supabase project
2. Run `database/schema.sql` in SQL Editor
3. This creates the `cards` table with RLS policies and triggers

## Deployment Workflow

### Initial Deploy to Vercel
1. Deploy frontend: `cd frontend && vercel`
2. Set environment variables on Vercel dashboard
3. Note the production URL (e.g., `https://tombola-xyz.vercel.app`)

### Generating Cards for Production
1. Update `BASE_URL` in `scripts/generate_cards.py` to match Vercel URL
2. Adjust `NUM_CARDS` if needed (default: 150)
3. Run `python generate_cards.py`
4. QR codes are saved to `scripts/qr_codes/` directory
5. Print QR codes and distribute to players

**Important**: QR codes contain hardcoded URLs. If you change the deployment URL, regenerate all QR codes. Either delete existing cards from database first or generate cards with new IDs.

## Key Files

- **`frontend/src/components/Card.jsx`** - Main game component (card display, number marking, Supabase integration)
- **`frontend/src/lib/supabaseClient.js`** - Supabase client initialization
- **`scripts/generate_cards.py`** - Card generation algorithm and QR code creation
- **`database/schema.sql`** - Complete database schema with RLS policies
- **`database/fix_rls.sql`** - Alternative RLS policy configuration if needed

## Customization Points

### Changing Number of Cards
Edit `NUM_CARDS` in `scripts/generate_cards.py` (default: 150)

### UI Styling
The Card component uses Tailwind CSS. Key customization areas:
- Color gradients: Search for `bg-gradient-to-br` classes
- Grid spacing: Modify `gap-` classes in the number grid
- Card dimensions: Adjust `aspect-` and size classes

### Background Image
Place custom card background at `frontend/public/assets/cartella-bg.png`. The number grid overlays this image with absolute positioning. May need to adjust padding (`p-4`) and gap (`gap-2`) in `Card.jsx` to align numbers with custom backgrounds.

## Tech Stack

- **Frontend**: React 19, Vite 7, Tailwind CSS 4
- **Backend**: Supabase (PostgreSQL with RLS)
- **Card Generation**: Python 3, NumPy, python-qrcode
- **Authentication**: Device UUID in localStorage (no traditional auth)
- **Deployment**: Vercel (frontend), Supabase (database)

## Common Issues

### "Cartella già presa" (Card Already Taken)
This is expected behavior - each card can only be claimed by one device. To test with the same card:
- Clear localStorage in browser DevTools
- Use incognito/private browsing
- Use a different browser

### QR Codes Point to Wrong URL
Update `BASE_URL` in `scripts/generate_cards.py` and regenerate all QR codes after deployment.

### RLS Policy Errors
If card claiming fails, check that `database/schema.sql` was run completely. Alternatively, try `database/fix_rls.sql` for alternative RLS configuration.

### Numbers Don't Align with Background Image
Adjust the grid overlay padding and gaps in `Card.jsx`:
```jsx
<div className="absolute inset-0 p-4">  // Adjust p-4
  <div className="grid grid-rows-3 gap-2 h-full">  // Adjust gap-2
```