#!/bin/bash
cd "$(dirname "$0")/frontend"
echo "🎨 Starting Zyndai Frontend..."
npm install
npm run dev
