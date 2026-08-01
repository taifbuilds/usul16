#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/deploy/usul16"

echo "Starting Usul16 deployment..."

cd "$APP_DIR"

echo "Pulling latest code..."
git fetch origin
git reset --hard origin/main

echo "Updating backend..."
cd "$APP_DIR/eshia-research"
source .venv/bin/activate
pip install -e .

echo "Building frontend..."
cd "$APP_DIR/web"
npm ci
npm run build

echo "Restarting services..."
sudo systemctl restart usul16-api
sudo systemctl restart usul16-web

echo "Checking services..."
sudo systemctl is-active --quiet usul16-api
sudo systemctl is-active --quiet usul16-web

echo "Deployment completed successfully."
