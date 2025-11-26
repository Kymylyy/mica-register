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

3. **Import CSV data:**
```bash
# Make sure casp-register.csv is in the root directory
python import_data.py
```

This will:
- Create the SQLite database
- Import all entities from `casp-register.csv`
- Normalize service codes to MiCA standard (a-j)
- Fix encoding issues (German characters, quotation marks)

4. **Run the server:**
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

Edit `frontend/src/index.css` to change the color scheme:

```css
:root {
  --color-primary: #3b82f6;      /* Primary blue */
  --color-secondary: #8b5cf6;    /* Secondary purple */
  --color-bg: #ffffff;            /* Background */
  --color-text: #1f2937;         /* Text color */
  --color-border: #e5e7eb;       /* Border color */
}
```

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

## Data Import

The CSV import process:
1. Tries multiple encodings (UTF-8, Latin-1, Windows-1252, etc.)
2. Fixes encoding issues (German characters, broken quotation marks)
3. Normalizes service codes to MiCA standard (a-j)
4. Handles pipe-separated values for services and passport countries
5. Creates relationships between entities, services, and countries

## Development

### Backend
- FastAPI with SQLAlchemy ORM
- SQLite database (can be easily switched to PostgreSQL)
- Automatic API documentation at `http://localhost:8000/docs`

### Frontend
- React 19 with Vite
- TanStack Table for advanced table features
- Tailwind CSS for styling
- Axios for API calls

## License

This project is for displaying publicly available ESMA data.

## Notes

- The database is created automatically on first import
- CSV file should be placed in the root directory
- Virtual environment and database files are gitignored
- The application handles up to 1000 entities per request (adjustable in API)
