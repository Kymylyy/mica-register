#!/bin/bash
# Script to import all register data to Railway production
# Usage: ./update_production.sh YOUR_RAILWAY_URL

if [ -z "$1" ]; then
    echo "Usage: ./update_production.sh YOUR_RAILWAY_URL"
    echo "Example: ./update_production.sh https://your-app.railway.app"
    exit 1
fi

RAILWAY_URL=$1
echo "=========================================="
echo "Importing ALL registers to Railway"
echo "=========================================="
echo ""
echo "Production URL: $RAILWAY_URL"
echo "Endpoint: POST /api/admin/import-all"
echo ""

# Import all 5 registers (CASP, OTHER, ART, EMT, NCASP)
echo "Calling import endpoint..."

# Check if jq is available for pretty printing
if command -v jq &> /dev/null; then
    curl -X POST "$RAILWAY_URL/api/admin/import-all" \
        -H "Content-Type: application/json" \
        -v \
        | jq .
else
    # Fallback without jq
    echo "(jq not found - showing raw JSON)"
    curl -X POST "$RAILWAY_URL/api/admin/import-all" \
        -H "Content-Type: application/json" \
        -v
fi

echo ""
echo "=========================================="
echo "Import Summary"
echo "=========================================="
echo ""
echo "Check the JSON response above for:"
echo "  - registers.casp.entities_count"
echo "  - registers.other.entities_count"
echo "  - registers.art.entities_count"
echo "  - registers.emt.entities_count"
echo "  - registers.ncasp.entities_count"
echo "  - total_entities"
echo ""
echo "Expected total: ~989 entities (149+705+1+32+102)"
echo ""
echo "If import failed, check Railway logs:"
echo "  railway logs --tail 100"
echo ""
echo "Alternative: Use Railway CLI to run import directly:"
echo "  railway run python backend/import_all_registers.py"
echo ""
