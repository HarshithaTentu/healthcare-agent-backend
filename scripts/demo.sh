#!/bin/bash
set -e

BASE_URL="http://127.0.0.1:8000"

echo "Checking Swagger..."
curl -s "$BASE_URL/docs" > /dev/null && echo "Swagger is reachable"

echo ""
echo "Calling /agent endpoint"
curl -s -X POST "$BASE_URL/agent" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is fever?"}' | python3 -m json.tool

echo ""
echo "Demo complete ✅"
