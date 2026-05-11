# Cravyo - AI-Powered Food Craving Detection & Smart Ordering Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.70-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Cravyo** analyzes your Instagram or YouTube feed, detects what food you're craving, and suggests the best way to order it on Swiggy -- with live price comparisons across **Food Delivery**, **Instamart**, and **Dineout**. It learns your preferences over time through a personalization memory layer.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [ZyndAI Agent (Optional)](#zyndai-agent-optional)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Agent Pipeline](#agent-pipeline)
- [Demo Presets](#demo-presets)
- [Supported Options](#supported-options)
- [Contributing](#contributing)
- [License](#license)

---

## Features

**Feed Analysis & Craving Detection**
- Scrapes Instagram posts (captions, hashtags, thumbnails) and YouTube videos (titles, descriptions, tags) via Apify
- Detects food items and cuisines using keyword matching + Groq LLM (Llama 3.3-70B)
- Confidence scoring for craving predictions

**Smart Ordering Suggestions**
- Time-aware delivery mode selection (Instamart for quick grocery, Food Delivery for meals, Dineout for dining out)
- Filters suggestions by dietary profile (Veg, Non-Veg, Vegan, Gym, Diet)
- Accounts for restaurant proximity

**Price Comparison Engine**
- Side-by-side cost breakdown across Swiggy Food Delivery, Instamart, and Dineout
- Includes base price, delivery fees, taxes, total cost, delivery time, and pros/cons
- Budget pick, fastest option, and best experience recommendations

**Personalization Memory**
- Tracks order history, favorite restaurants (scored), favorite dishes, and cuisine preferences
- Skips restaurants you don't want to see again
- Order ratings (1-5 stars) influence future suggestions
- Persistent JSON-based storage that learns over time

**Analytics Dashboard**
- 30-day craving trend charts (area, pie, bar)
- Order statistics: total spent, average rating, healthy order percentage
- Channel distribution breakdown and nutrition overview
- AI-generated smart insights

**A2A Agent (ZyndAI Network)**
- Full Agent-to-Agent (A2A) protocol support via JSON-RPC 2.0
- Multi-platform craving fusion engine (Instagram, YouTube, Twitter, Reddit, and more)
- Meal nudge engine with time-aware urgency notifications
- Desktop notifications (Windows), webhook, and log backends
- Discoverable on the ZyndAI agent registry

---

## Architecture

```
                    +------------------+
                    |   React Frontend |  (Vite, port 5173)
                    |   Dashboard UI   |
                    +--------+---------+
                             |
                        /api proxy
                             |
                    +--------v---------+
                    |  FastAPI Backend  |  (Uvicorn, port 8000)
                    |   REST API Layer  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v--------+
     |  Instagram  |  |   YouTube   |  |   Swiggy    |
     |  Scraper    |  |   Scraper   |  |   Service   |
     |  (Apify)    |  |   (Apify)   |  |   (Mock)    |
     +-------------+  +-------------+  +-------------+
              |              |              |
              +--------------+--------------+
                             |
                    +--------v---------+
                    | LangGraph Agent  |
                    | Pipeline (Groq)  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v--------+
     | Price       |  | Memory      |  | Craving     |
     | Comparison  |  | Layer       |  | Trends      |
     +-------------+  +-------------+  +-------------+
```

---

## Tech Stack

### Backend (Python)
| Technology | Purpose |
|---|---|
| **FastAPI** | REST API framework |
| **LangGraph** | Stateful agent pipeline (StateGraph) |
| **LangChain + Groq** | LLM integration (Llama 3.3-70B-Versatile) |
| **Apify** | Instagram & YouTube web scraping |
| **Pydantic** | Request/response validation |
| **BeautifulSoup4** | Fallback YouTube scraping |

### Frontend (JavaScript)
| Technology | Purpose |
|---|---|
| **React 18** | UI library |
| **Vite** | Build tool & dev server |
| **Recharts** | Interactive charts & analytics |

### ZyndAI Agent
| Technology | Purpose |
|---|---|
| **zyndai-agent SDK** | A2A protocol agent framework |
| **LangChain AgentExecutor** | Natural language tool-calling agent |
| **Win10Toast** | Desktop notification backend |

---

## Project Structure

```
cravyo-mvp/
├── backend/                          # FastAPI Python server
│   ├── main.py                       # All REST API endpoints
│   ├── feed_analyzer_agent.py        # LangGraph agent pipeline
│   ├── instagram_service.py          # Apify Instagram scraper
│   ├── youtube_service.py            # Apify YouTube scraper + BS4 fallback
│   ├── swiggy_service.py             # Mock Swiggy API (restaurant catalogue)
│   ├── nodes/
│   │   ├── personalization_memory.py # User memory class + LangGraph nodes
│   │   └── price_comparison_node.py  # LLM-powered price comparison
│   ├── requirements.txt
│   ├── .env.example
│   ├── user_preferences.json         # Persistent user memory (runtime)
│   └── craving_trends.json           # Craving history (runtime)
│
├── frontend/                         # React SPA (Vite)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js                # Dev server proxy config
│   └── src/
│       ├── main.jsx                  # React entry point
│       └── App.jsx                   # Full UI (single-file component)
│
├── cravyo-agent/                     # ZyndAI A2A network agent
│   ├── agent.py                      # Agent entry point
│   ├── agent.config.json             # Agent metadata & skills
│   ├── payload.py                    # Pydantic request/response schemas
│   ├── A2A_API.md                    # A2A protocol reference
│   ├── requirements.txt
│   ├── .env.example
│   ├── .well-known/
│   │   └── agent-card.json           # A2A agent discovery card
│   └── backend/                      # Embedded backend for agent
│       ├── feed_analyzer_agent.py
│       ├── fusion_engine.py          # Multi-platform craving fusion
│       ├── meal_nudge_engine.py      # Time-aware meal nudges
│       ├── notification.py           # Desktop/webhook/log notifications
│       └── nodes/
│           ├── personalization_memory.py
│           └── price_comparison_node.py
│
├── start-backend.sh                  # Backend startup script
├── start-frontend.sh                 # Frontend startup script
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Groq API Key** -- [Get one here](https://console.groq.com)
- **Apify API Token** -- [Get one here](https://apify.com) (required for real feed scraping; demo presets work without it)

### Environment Variables

Create a `.env` file inside the `backend/` directory:

```env
APIFY_API_TOKEN=your_apify_token_here
GROQ_API_KEY=your_groq_api_key_here
SWIGGY_API_KEY=your_swiggy_api_key_here    # Optional (mock data used)
TAVILY_API_KEY=your_tavily_api_key_here    # Optional
```

> **Note:** The Swiggy integration currently uses mock data with realistic restaurant catalogues. No real Swiggy API key is needed.

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

Backend runs at **http://localhost:8000**
Interactive API docs at **http://localhost:8000/docs**

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:5173**

> The Vite dev server proxies `/api/*` requests to the backend at `localhost:8000`.

### ZyndAI Agent (Optional)

The ZyndAI agent wraps the backend as an A2A-compatible network agent, allowing other AI agents to discover and call Cravyo.

```bash
cd cravyo-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and ZyndAI keypair path

# Start the agent
python agent.py
```

Agent runs at **http://localhost:5000** and registers on the ZyndAI network.

---

## Usage

### 1. Analyze Tab
Select a **demo preset** (Indian, Chinese, Italian, Snacks, Gym) or enter a real **Instagram/YouTube username**. Choose your dietary profile and proximity preference, then hit analyze. The agent will:
- Scrape the feed (or use demo posts)
- Detect food items and cuisine
- Suggest the best ordering channel
- Show a price comparison table

### 2. Price Compare Tab
Enter any **dish name** and **city** to get a structured cost comparison across all three Swiggy channels, with recommendations for budget, speed, and experience.

### 3. Memory Tab
View your **personalization profile** -- favorite restaurants, top dishes, and order history. Record new orders, skip restaurants, and see how your preferences evolve.

### 4. Trends Tab
Visualize your **30-day craving trends** with interactive charts showing cuisine distribution, weekly patterns, and top cravings.

### 5. Stats Tab
Full **ordering analytics** -- total spend, average ratings, healthy order percentage, channel distribution, nutrition overview, and AI-generated insights.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + config status |
| `POST` | `/analyze` | Full pipeline with real Instagram/YouTube scraping |
| `POST` | `/analyze/mock` | Pipeline with custom posts (no scraping needed) |
| `POST` | `/price-compare` | Compare dish prices across all channels |
| `POST` | `/order` | Record a confirmed order to memory |
| `POST` | `/skip` | Skip/dismiss a restaurant from suggestions |
| `POST` | `/rate-last-order` | Rate your most recent order (1-5) |
| `GET` | `/memory` | Get user preferences and order history |
| `DELETE` | `/memory` | Clear all preferences and start fresh |
| `GET` | `/trends` | Craving trend data (30-day window) |
| `GET` | `/demo-posts/{preset}` | Get mock posts for a cuisine preset |

Full interactive API documentation is available at `/docs` when the backend is running.

---

## Agent Pipeline

The core craving detection pipeline is built with **LangGraph** as a stateful directed graph:

```
load_memory -> scrape_feed -> analyze_food -> [food detected?]
                                                  |
                                         Yes      |      No
                                          |       v       |
                                          v    (END)      v
                              decide_swiggy_mode       (END)
                                          |
                                          v
                                   compare_prices
                                          |
                                          v
                                     call_swiggy
                                          |
                                          v
                                     save_memory
                                          |
                                          v
                                        (END)
```

**Pipeline Steps:**
1. **Load Memory** -- Retrieves user preferences from persistent storage
2. **Scrape Feed** -- Fetches posts from Instagram or YouTube via Apify
3. **Analyze Food** -- Detects food items using keyword matching + Groq LLM
4. **Decide Mode** -- Selects delivery mode based on time of day, dietary profile, and proximity
5. **Compare Prices** -- Generates cost breakdown across Instamart, Food Delivery, and Dineout
6. **Call Swiggy** -- Fetches matching restaurants/items filtered by dietary needs and skipped restaurants
7. **Save Memory** -- Persists updated preferences and craving trends

---

## Demo Presets

Try these built-in presets without needing any API keys for scraping:

| Preset | Cuisine | Sample Posts |
|--------|---------|-------------|
| `indian` | Indian | Biryani, butter chicken, dosa, paneer tikka |
| `chinese` | Chinese | Noodles, dumplings, manchurian, fried rice |
| `italian` | Italian | Pizza, pasta, risotto, bruschetta |
| `snacks` | Mixed Snacks | Samosa, vada pav, spring rolls, momos |
| `gym` | Healthy/Fitness | Protein bowls, salads, smoothies, grilled chicken |

---

## Supported Options

**Dietary Profiles:** All, Veg, Non-Veg, Gym, Diet, Vegan

**Cuisines:** Indian, Chinese, Italian, Thai, Mexican, American, Desserts, Healthy

**Cities (Price Comparison):** Pune (default), Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Kolkata

**Platforms:** Instagram, YouTube

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m 'Add your feature'`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

Built with LangGraph, Groq, and Apify.
