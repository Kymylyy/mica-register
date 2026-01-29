# MiCA Register

Web application to display and filter ESMA MiCA registers data. A simple, fast, and user-friendly database interface for exploring all 5 EU MiCA registers:
- **CASP** - Crypto-Asset Service Providers
- **OTHER** - White Papers for other crypto-assets
- **ART** - Asset-Referenced Token Issuers
- **EMT** - E-Money Token Issuers
- **NCASP** - Non-Compliant Entities

## Features

### Core Functionality
- **Multi-register support** - Browse all 5 ESMA MiCA registers with tab-based navigation
- **Display entities** from ESMA registers with register-specific fields
- **Advanced filtering**:
  - Search by name, address, website, LEI, or other fields
  - Filter by Home Member State (multi-select with country flags)
  - Filter by Crypto-asset services (CASP only: MiCA standard services a-j)
  - Filter by Authorisation / notification date range
  - Register-specific filters (e.g., credit institution for ART, exemptions for EMT)
- **Dynamic filter counts** - See how many entities match each filter option in real-time
- **Sortable table** with column visibility toggle and register-specific columns
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
- **Tab-based register navigation** with clear visual indication of active register

## Project Structure

```
mica-register/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py      # SQLAlchemy database setup
│   │   ├── models.py        # Multi-register database models
│   │   │                    # - Base Entity + extension tables per register
│   │   │                    # - CaspEntity, OtherEntity, ArtEntity, EmtEntity, NcaspEntity
│   │   ├── schemas.py       # Pydantic schemas for API
│   │   ├── main.py          # FastAPI app initialization
│   │   ├── import_csv.py    # Multi-register CSV import logic
│   │   ├── config/
│   │   │   └── registers.py # Register configuration and mappings
│   │   └── routers/
│   │       └── entities.py  # API endpoints (with register_type parameter)
│   ├── requirements.txt     # Python dependencies
│   └── database.db         # SQLite database (created after import)
├── frontend/                # React + Vite frontend
│   ├── src/
│   │   ├── main.jsx         # React Router setup
│   │   ├── App.jsx          # Main application component (register-aware)
│   │   ├── components/
│   │   │   ├── RegisterSelector.jsx  # Tab-based register navigation
│   │   │   ├── DataTable.jsx         # Table with register-specific columns
│   │   │   ├── Filters.jsx           # Dynamic filters per register
│   │   │   ├── FlagIcon.jsx          # Country flag utilities
│   │   │   └── TagManager.jsx        # Tag management (optional)
│   │   ├── config/
│   │   │   └── registerColumns.js    # Column definitions per register
│   │   └── utils/
│   │       ├── serviceDescriptions.js  # MiCA service mappings
│   │       └── modalUtils.js           # Modal utilities
│   ├── package.json
│   └── tailwind.config.js
├── scripts/                 # Data management scripts
│   ├── update_esma_data.py  # Orchestration script (all 5 registers)
│   ├── check_esma_update.py # Check ESMA for updates
│   ├── validate_csv.py      # CSV validation
│   ├── clean_csv.py         # CSV cleaning
│   └── import_*.py          # Register-specific import scripts
├── data/                    # CSV data files
│   ├── raw/
│   │   ├── casp/            # CASP CSV files (CASPyyyymmdd.csv)
│   │   ├── other/           # OTHER CSV files (OTHERyyyymmdd.csv)
│   │   ├── art/             # ART CSV files (ARTyyyymmdd.csv)
│   │   ├── emt/             # EMT CSV files (EMTyyyymmdd.csv)
│   │   └── ncasp/           # NCASP CSV files (NCASPyyyymmdd.csv)
│   └── cleaned/             # Cleaned versions (future)
├── venv/                    # Python virtual environment (not in git)
└── README.md
```

## Architecture

### Multi-Register Database Design

The application uses a **hybrid architecture** with a base Entity table and extension tables for register-specific fields:

```
entities (common fields)
├── register_type: casp|other|art|emt|ncasp
├── competent_authority, home_member_state, lei, lei_name, etc.
├── commercial_name, address, website, authorisation_notification_date
└── Extension tables (1:1 relationships):
    ├── casp_entities (services, passport_countries, website_platform)
    ├── other_entities (white_paper_url, offer_countries, dti_codes, lei_casp)
    ├── art_entities (credit_institution, white_paper_notification_date)
    ├── emt_entities (exemption_48_4, exemption_48_5, dti_codes)
    └── ncasp_entities (websites, infringement, reason, decision_date)
```

**Benefits:**
- Single query with one join per register
- Type safety with SQLAlchemy models
- Easy to extend with new registers
- Computed properties expose register-specific fields in API
- Efficient filtering with register_type index

### API Design

All endpoints accept a `register_type` query parameter:

```
GET /api/entities?register_type=casp
GET /api/entities?register_type=other
GET /api/entities?register_type=art
GET /api/entities?register_type=emt
GET /api/entities?register_type=ncasp
```

The API automatically filters entities and applies register-specific logic (e.g., service codes only for CASP).

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

   **Option A: Import all registers**
   ```bash
   python app/import_csv.py --all
   ```

   **Option B: Import specific register**
   ```bash
   python app/import_csv.py --register casp
   python app/import_csv.py --register other
   python app/import_csv.py --register art
   python app/import_csv.py --register emt
   python app/import_csv.py --register ncasp
   ```

This will:
- Create the database (PostgreSQL or SQLite based on DATABASE_URL)
- Import entities from the latest CSV file in `data/raw/{register}/`
- Create extension tables and relationships
- Normalize service codes to MiCA standard (CASP: a-j)
- Fix encoding issues (German characters, quotation marks)

5. **Run the server:**
```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Configure API URL (optional):**

   Create `frontend/.env`:
   ```
   VITE_API_URL=http://localhost:8000
   ```

3. **Run development server:**
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

## Updating Data

### Automated Update (Recommended)

Use the orchestration script to download the latest data for all registers:

```bash
# Update all registers
python scripts/update_esma_data.py --all

# Update specific register
python scripts/update_esma_data.py --register casp

# Force re-download even if file exists
python scripts/update_esma_data.py --all --force
```

The script will:
1. Check ESMA website for the latest update date
2. Download CSV files for selected registers
3. Save files to `data/raw/{register}/`
4. Update frontend "Last updated" date

After download, import the data:
```bash
# Import all registers
python backend/app/import_csv.py --all

# Or import specific register
python backend/app/import_csv.py --register casp
```

### Manual Update

1. Download CSV files from ESMA:
   - CASP: https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv
   - OTHER: https://www.esma.europa.eu/sites/default/files/2024-12/OTHER.csv
   - ART: https://www.esma.europa.eu/sites/default/files/2024-12/ARTZZ.csv
   - EMT: https://www.esma.europa.eu/sites/default/files/2024-12/EMTWP.csv
   - NCASP: https://www.esma.europa.eu/sites/default/files/2024-12/NCASP.csv

2. Save files to respective directories:
   - `data/raw/casp/CASP20260129.csv`
   - `data/raw/other/OTHER20260129.csv`
   - etc.

3. Import to database:
   ```bash
   python backend/app/import_csv.py --all
   ```

## API Endpoints

### Entities
- `GET /api/entities` - List entities with filtering
  - Query params:
    - `register_type` (required): casp|other|art|emt|ncasp
    - `search`: Search text
    - `home_member_states[]`: Filter by countries
    - `service_codes[]`: Filter by services (CASP only)
    - `auth_date_from`, `auth_date_to`: Date range
    - `skip`, `limit`: Pagination
- `GET /api/entities/{id}` - Get single entity details
- `GET /api/entities/count` - Get count with filters applied
- `PATCH /api/entities/{id}` - Update entity (currently supports comments)

### Filters
- `GET /api/filters/options` - Get available filter options per register
  - Query params: `register_type`
- `GET /api/filters/counts` - Get dynamic counts for filter options
  - Query params: `register_type` + filter params

### Tags (Optional)
- `POST /api/entities/{id}/tags` - Add tag to entity
- `DELETE /api/entities/{id}/tags/{tag_name}` - Remove tag

## MiCA Service Codes (CASP Register)

The CASP register uses standard MiCA service codes (a-j):

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

## Register-Specific Fields

### CASP (Crypto-Asset Service Providers)
- Services (a-j)
- Passport countries
- Website platform
- Authorisation end date

### OTHER (White Papers)
- White paper URL, comments, last update
- Offer countries (pipe-separated)
- DTI codes and FFG flag
- Linked CASP LEI and name

### ART (Asset-Referenced Tokens)
- Credit institution flag
- White paper URL, notification date, offer countries
- White paper comments and last update
- Authorisation end date

### EMT (E-Money Tokens)
- Exemption 48.4 and 48.5 flags
- Authorisation for other EMT
- DTI codes and FFG flag
- White paper URL, notification date, comments
- Authorisation end date

### NCASP (Non-Compliant Entities)
- Multiple websites (pipe-separated)
- Infringement description
- Reason for non-compliance
- Decision date

## Data Import Pipeline

The CSV import process follows a multi-stage pipeline:

### 1. Download
- Automated download from ESMA website
- Validates file exists and is accessible
- Saves to `data/raw/{register}/`

### 2. Validation (Future)
- Detects encoding (UTF-8, Latin-1, Windows-1252, etc.)
- Validates CSV structure, schema, and data formats
- Identifies errors and warnings
- Generates validation reports

### 3. Cleaning (Future - Deterministic)
- Fixes encoding issues (German characters, broken quotation marks)
- Normalizes service codes to MiCA standard (a-j)
- Fixes date formats (DD/MM/YYYY)
- Merges duplicate LEI entries
- Normalizes country codes and commercial names
- Handles pipe-separated values
- Generates cleaning reports

### 4. Import
- Imports CSV to database
- Creates base Entity records
- Creates extension table records per register
- Creates relationships (services, passport_countries for CASP)
- Handles register-specific fields and validation

## Development

### Backend
- FastAPI with SQLAlchemy ORM
- PostgreSQL database (with SQLite fallback for local development)
- Multi-register architecture with base + extension tables
- Automatic API documentation at `http://localhost:8000/docs`
- Database URL configured via `DATABASE_URL` environment variable

### Frontend
- React 19 with Vite
- React Router for multi-register navigation
- TanStack Table for advanced table features
- Tailwind CSS for styling
- Axios for API calls
- Register-aware components with dynamic columns and filters

## Performance Optimizations

### Backend
- **Database indexes** on frequently queried fields:
  - `register_type` + `home_member_state` composite index
  - `authorisation_notification_date` for date filtering
  - `commercial_name` for search
  - `lei` for lookups
- **GROUP BY queries** for filter counts (15-25x faster than multiple COUNT queries)
- **Lazy loading** for relationships (only load when needed)
- **Connection pooling** with optimized pool size

### Frontend
- **Debounced search** (300ms) to prevent excessive API calls
- **Batch API requests** using Promise.all
- **Cached filter counts** to avoid redundant requests
- **Register-based partitioning** (only load active register data)

### Expected Performance
- Entity listing: <150ms
- Entity count: <50ms
- Filter counts: <200ms (down from 3-5 seconds)
- Register switching: <500ms

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
   - Railway will use the Dockerfile in the root directory

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

### First Data Import / Updating Production Data

After deployment, import data to production database:

1. **Update local data:**
   ```bash
   python scripts/update_esma_data.py --all
   ```

2. **Commit and push:**
   ```bash
   git add data/raw/ frontend/src/App.jsx
   git commit -m "Update ESMA data to 29 January 2026"
   git push
   ```

3. **Import to production:**
   ```bash
   # Call Railway import endpoint
   curl -X POST https://your-app.railway.app/api/admin/import \
     -H "Content-Type: application/json" \
     -d '{"register_type": "all"}'
   ```

   Or import specific register:
   ```bash
   curl -X POST https://your-app.railway.app/api/admin/import \
     -H "Content-Type: application/json" \
     -d '{"register_type": "casp"}'
   ```

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

## Current Status

### Completed (v2.0)
- ✅ All 5 ESMA MiCA registers implemented
- ✅ Multi-register database architecture
- ✅ Tab-based navigation between registers
- ✅ Register-specific columns and filters
- ✅ Dynamic API with register_type parameter
- ✅ Performance optimizations (15-25x faster filter counts)
- ✅ Automated data update script for all registers
- ✅ Register-specific entity details modals

### Current Entities Count
- CASP: 132 entities
- OTHER: 594 entities
- ART: 0 entities (empty but ready)
- EMT: 17 entities
- NCASP: 101 entities
- **Total: 844 entities**

### Future Enhancements (Optional)
- Per-register "Last updated" display
- Validation and cleaning pipeline for all registers
- LLM remediation for data quality
- Cross-register search (find same LEI across registers)
- Comparison view (compare entity across registers)
- Export functionality (CSV/Excel per register)
- Statistics dashboard
- Email alerts for new NCASP entries

## License

This project is for displaying publicly available ESMA data.

## Notes

- The database is created automatically on first import
- Virtual environment and database files are gitignored
- The application handles up to 1000 entities per request (adjustable in API)
- **Database:** Uses PostgreSQL when `DATABASE_URL` environment variable is set, otherwise falls back to SQLite for local development
- **Production:** Set `DATABASE_URL` environment variable to your PostgreSQL connection string (format: `postgresql://user:password@host:port/database`)
- **Multi-register:** All 5 registers share the same database with register_type discriminator
