# Medical AI System

Production-ready medical AI API with RAG system for French medication database.

## Features
- 🧠 RAG (Retrieval-Augmented Generation) system
- 🤖 Fine-tuned medical models
- 🌐 Flask REST API
- 📱 SwiftUI integration ready

## Deployment
This repository is optimized for Railway deployment.

### Environment Variables Required:
- `OPENAI_API_KEY`: Your OpenAI API key
- `FLASK_ENV`: Set to `production`

### Endpoints:
- `GET /health` - Health check
- `POST /query` - Ask medical questions
- `POST /search` - Search medications
- `GET /medication/<cis>` - Get medication by CIS code

## Usage
Deploy to Railway and update your SwiftUI app baseURL to the Railway URL.
