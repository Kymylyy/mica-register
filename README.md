# MiCA Register

Web application to display and filter ESMA crypto-asset service providers data. A simple, fast, and user-friendly database interface for exploring licensed crypto-asset service providers in the EU.

## Features

### Core Functionality
- **Display crypto-asset service providers** from ESMA register
- **Advanced filtering**:
  - Search by name, address, website, or service descriptions
  - Filter by Home Member State (multi-select with country flags)
  - Filter by Crypto-asset services (multi-select, MiCA standard services a-j)
  - Filter by Authorisation / notification date range
- **Dynamic filter counts** - See how many entities match each filter option in real-time
- **Sortable table** with column visibility toggle
- **Entity details modal** with full information and keyboard navigation
- **Country flags** display for better visual identification
- **Responsive design** with easy color customization

### User Experience
- **Debounced search** (100ms) for smooth typing experience
- **Collapsible filters** with real-time search within filter options
- **Short service names** in table (e.g., "Custody", "Trading platform")
- **Full MiCA descriptions** in modal and filters with proper capitalization
- **Services sorted** by MiCA order (a-j)
- **Copy-to-clipboard** functionality for LEI, address, and website
- **Keyboard navigation** (ESC to close, arrow keys to navigate entities)

## Project Structure

```
mica-register/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py      # SQLAlchemy database setup
│   │   ├── models.py         # Database models (Entity, Service, etc.)
│   │   ├── schemas.py        # Pydantic schemas for API
│   │   ├── main.py          # FastAPI app initialization
│   │   ├── import_csv.py    # CSV import logic with encoding fixes
│   │   └── routers/
│   │       └── entities.py  # API endpoints
│   ├── import_data.py       # Script to import CSV data
│   ├── requirements.txt     # Python dependencies
│   └── database.db         # SQLite database (created after import)
├── frontend/                # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx          # Main application component
│   │   ├── components/
│   │   │   ├── DataTable.jsx    # Table component with sorting
│   │   │   ├── Filters.jsx      # Filter controls
│   │   │   ├── FlagIcon.jsx     # Country flag utilities
│   │   │   └── TagManager.jsx  # Tag management (optional)
│   │   └── utils/
│   │       ├── serviceDescriptions.js  # MiCA service mappings
│   │       └── modalUtils.js           # Modal utilities
│   ├── package.json
│   └── tailwind.config.js
├── casp-register.csv        # Source CSV file from ESMA
├── venv/                    # Python virtual environment (not in git)
└── README.md
```

## Setup

### Prerequisites
- Python 3.11+ 
- Node.js 18+ and npm
- Git

### Backend Setup

1. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

3. **Database Configuration:**

   **Option A: PostgreSQL (Recommended for production)**
   ```bash
   # Set DATABASE_URL environment variable
   export DATABASE_URL="postgresql://user:password@localhost:5432/mica_register"
   # Or create a .env file with:
   # DATABASE_URL=postgresql://user:password@localhost:5432/mica_register
   ```
   
   **Option B: SQLite (Default for local development)**
   ```bash
   # No configuration needed - SQLite will be used automatically
   # if DATABASE_URL is not set
   ```

4. **Import CSV data:**
```bash
# Make sure casp-register.csv is in the root directory
python import_data.py
```

This will:
- Create the database (PostgreSQL or SQLite based on DATABASE_URL)
- Import all entities from `casp-register.csv`
- Normalize service codes to MiCA standard (a-j)
- Fix encoding issues (German characters, quotation marks)

5. **Run the server:**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Run development server:**
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Production Build

To build the frontend for production:
```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

## Customizing Colors

The project uses a centralized color system based on CSS variables. All colors are defined in `frontend/src/index.css` and automatically mapped to Tailwind classes.

### Quick Color Change

To change the entire color scheme, edit the CSS variables in `frontend/src/index.css`:

```css
:root {
  --color-primary-500: #3b82f6;  /* Change to your primary color */
  --color-primary-600: #2563eb;  /* Darker shade */
  --color-primary-700: #1d4ed8;  /* Even darker */
  /* ... full scale from 50 to 900 available */
}
```

### Available Color Scales

- `primary` - Main brand/accent color (used for buttons, links, focus states)
- `secondary` - Alternative accent
- `sky` - Service badges and light accents
- `slate` - Neutral UI elements (headers, borders, text)
- `gray` - Base grays (backgrounds, dividers)
- `red` - Error/destructive actions
- `green` - Success states

**Note:** The codebase currently uses a mix of direct Tailwind classes and CSS variables. Changing CSS variables will affect all elements using the variable-based classes. For full control, components can be gradually migrated to use the new system.

## API Endpoints

### Entities
- `GET /api/entities` - List entities with filtering
  - Query params: `search`, `home_member_states[]`, `service_codes[]`, `auth_date_from`, `auth_date_to`, `skip`, `limit`
- `GET /api/entities/{id}` - Get single entity details
- `GET /api/entities/count` - Get count with filters applied
- `PATCH /api/entities/{id}` - Update entity (currently supports comments)

### Filters
- `GET /api/filters/options` - Get available filter options (countries, services)
- `GET /api/filters/counts` - Get dynamic counts for filter options with current filters applied

### Tags (Optional)
- `POST /api/entities/{id}/tags` - Add tag to entity
- `DELETE /api/entities/{id}/tags/{tag_name}` - Remove tag

## MiCA Service Codes

The application uses standard MiCA service codes (a-j):

- **a** - Providing custody and administration of crypto-assets on behalf of clients
- **b** - Operation of a trading platform for crypto-assets
- **c** - Exchange of crypto-assets for funds
- **d** - Exchange of crypto-assets for other crypto-assets
- **e** - Execution of orders for crypto-assets on behalf of clients
- **f** - Placing of crypto-assets
- **g** - Reception and transmission of orders for crypto-assets on behalf of clients
- **h** - Providing advice on crypto-assets
- **i** - Providing portfolio management on crypto-assets
- **j** - Providing transfer services for crypto-assets on behalf of clients

## Data Import Pipeline

The CSV import process follows a multi-stage pipeline:

### 1. Validation
- Detects encoding (UTF-8, Latin-1, Windows-1252, etc.)
- Validates CSV structure, schema, and data formats
- Identifies errors and warnings
- Generates validation reports

### 2. Cleaning (Deterministic)
- Fixes encoding issues (German characters, broken quotation marks)
- Normalizes service codes to MiCA standard (a-j)
- Fixes date formats (DD/MM/YYYY)
- Merges duplicate LEI entries
- Normalizes country codes and commercial names
- Handles pipe-separated values for services and passport countries
- Generates cleaning reports

### 3. LLM Remediation (Optional)
- Uses Gemini API to fix edge cases that deterministic cleaning couldn't handle
- Operates with strict guardrails and full auditability
- Only processes remaining errors after deterministic cleaning
- Generates remediation patches with confidence scores

### 4. Import
- Imports cleaned CSV to database
- Creates relationships between entities, services, and countries
- Automatically finds the newest cleaned CSV file

See `UPDATE_DATA.md` for detailed instructions on updating data.

## Development

### Backend
- FastAPI with SQLAlchemy ORM
- PostgreSQL database (with SQLite fallback for local development)
- Automatic API documentation at `http://localhost:8000/docs`
- Database URL configured via `DATABASE_URL` environment variable

### Frontend
- React 19 with Vite
- TanStack Table for advanced table features
- Tailwind CSS for styling
- Axios for API calls

## Deployment

### Frontend (Vercel)

1. **Connect your GitHub repository to Vercel**
   - Go to [vercel.com](https://vercel.com) and sign in
   - Click "New Project" and import your repository
   - Set root directory to `frontend`

2. **Configure Environment Variables**
   - In Vercel project settings, add:
     - `VITE_API_URL` = Your Railway backend URL (e.g., `https://your-app.railway.app`)

3. **Deploy**
   - Vercel will automatically build and deploy on every push to main branch

### Backend (Railway)

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app) and sign in with GitHub

2. **Create New Project**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will use the Dockerfile in the root directory (configured in `railway.json`)

3. **Add PostgreSQL Database**
   - In Railway project, click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable

4. **Configure Environment Variables**
   - In Railway project settings, add:
     - `CORS_ORIGINS` = Your Vercel frontend URL (e.g., `https://your-app.vercel.app`)
     - `DATABASE_URL` = Automatically set by Railway PostgreSQL service

5. **Deploy**
   - Railway will automatically build from Dockerfile and deploy
   - Get your backend URL from Railway (e.g., `https://your-app.railway.app`)

6. **Update Frontend Environment Variable**
   - Go back to Vercel and update `VITE_API_URL` with your Railway backend URL

### First Data Import / Updating Data

After deployment or when CSV data is updated, follow the complete pipeline:

1. **Validate raw CSV:**
   ```bash
   python scripts/validate_csv.py data/raw/CASP20251215.csv
   ```

2. **Clean CSV:**
   ```bash
   python scripts/clean_csv.py --input data/raw/CASP20251215.csv
   ```

3. **Optional: LLM Remediation** (if errors remain):
   ```bash
   python scripts/generate_remediation_tasks.py data/cleaned/CASP20251215_clean.csv reports/validation/clean/validation_CASP20251215_clean.json
   python scripts/run_llm_remediation.py reports/remediation/tasks/tasks_CASP20251215_clean.json
   python scripts/apply_remediation_patch.py data/cleaned/CASP20251215_clean.csv reports/remediation/patches/patch_*.json reports/remediation/tasks/tasks_CASP20251215_clean.json
   ```

4. **Import to database:**
   ```bash
   curl -X POST https://your-app.railway.app/api/admin/import
   ```
   Or use the provided script:
   ```bash
   ./update_production.sh https://your-app.railway.app
   ```

**Note:** After pushing new CSV data to GitHub:
- Railway automatically rebuilds with the new CSV file
- You must call the `/api/admin/import` endpoint to update the database
- Vercel automatically redeploys the frontend

See `UPDATE_DATA.md` for detailed step-by-step instructions.

## License

This project is for displaying publicly available ESMA data.

## Current Status

The application is in active development. Production deployment is ready - see Deployment section above.

### Known Issues
- "Last updated" timestamp in header shows placeholder - needs API endpoint
- Automatic data download from ESMA website not yet implemented (planned for cron job automation)

## Notes

- The database is created automatically on first import
- CSV file should be placed in the root directory
- Virtual environment and database files are gitignored
- The application handles up to 1000 entities per request (adjustable in API)
- **Database:** Uses PostgreSQL when `DATABASE_URL` environment variable is set, otherwise falls back to SQLite for local development
- **Production:** Set `DATABASE_URL` environment variable to your PostgreSQL connection string (format: `postgresql://user:password@host:port/database`)
