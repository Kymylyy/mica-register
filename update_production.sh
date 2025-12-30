#!/bin/bash
# Script to update data on Railway production
# Usage: ./update_production.sh YOUR_RAILWAY_URL

if [ -z "$1" ]; then
    echo "Usage: ./update_production.sh YOUR_RAILWAY_URL"
    echo "Example: ./update_production.sh https://your-app.railway.app"
    exit 1
fi

RAILWAY_URL=$1
echo "Importing data to Railway at: $RAILWAY_URL"
echo "Calling POST $RAILWAY_URL/api/admin/import"

curl -X POST "$RAILWAY_URL/api/admin/import" \
    -H "Content-Type: application/json" \
    -v

echo ""
echo "Done! Check the response above for confirmation."

