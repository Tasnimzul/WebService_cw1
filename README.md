# WebService_cw1

# Skincare & Ingredient Analysis API

A data-driven RESTful API for skincare product recommendations, ingredient safety analysis, and conflict detection. Built with FastAPI and backed by real product data from Lookfantastic (1,138 products) and a dermatological skin concern dataset.

**Module:** COMP3011 Web Services — University of Leeds  
**Student:** Tasnim Zulkifli  
**GitHub:** https://github.com/Tasnimzul/WebService_cw1  
**Live API:** https://comp3011-skincare.onrender.com  

> **Note:** The API is hosted on Render's free tier and may take up to 50 seconds to respond on the first request after a period of inactivity.

---

## Features

- Browse and search more than 1,000 real skincare products
- Ingredient safety scoring (0–10) based on irritation levels
- Ingredient conflict detection across multiple products
- Personalised skin profile and product recommendations
- Fuzzy ingredient matching using `rapidfuzz` to handle naming inconsistencies across datasets
- JWT authentication with rate limiting
- MCP (Model Context Protocol) server for AI assistant integration
- Admin panel for user and conflict management
- Full CRUD for products and user accounts
- Interactive frontend served at `/`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy |
| Validation | Pydantic v2 |
| Authentication | JWT (python-jose + passlib/bcrypt) |
| Rate Limiting | slowapi |
| Fuzzy Matching | rapidfuzz |
| Testing | pytest + FastAPI TestClient |
| Server | Uvicorn |
| Frontend | Vanilla HTML/CSS/JavaScript |

---

## Live Demo

| URL | Description |
|---|---|
| https://comp3011-skincare.onrender.com | Frontend application |
| https://comp3011-skincare.onrender.com/docs | Interactive Swagger UI |
| https://comp3011-skincare.onrender.com/redoc | ReDoc documentation |

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Tasnimzul/WebService_cw1.git
cd WebService_cw1
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

The default `.env` values work out of the box for local development.

### 5. Import data into the database

Run the import scripts in this order:

```bash
python data/import_concerns.py
python data/import_products.py
python data/import_conflicts.py
```

This populates the database with 1,138 products, skin concern data, and ingredient conflict pairs.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

---

## Local Usage

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Frontend application |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc documentation |

---

## API Documentation

Full API documentation is available in [API_documentation.pdf](./API_documentation.pdf)

Live interactive documentation: https://comp3011-skincare.onrender.com/docs

Authentication is handled via JWT Bearer tokens. Obtain a token by calling `POST /auth/login` and include it in the `Authorization: Bearer <token>` header for protected endpoints. Unauthenticated requests to protected endpoints return 401.

---

## Running Tests

```bash
TESTING=true venv/bin/python -m pytest tests/ -v
```

64 tests covering all endpoints including authentication, CRUD, analytics, and error handling. Tests use a separate in-memory database and never touch the production database.

---

## Key API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Login and receive JWT token |

### Products
| Method | Endpoint | Description |
|---|---|---|
| GET | `/products/` | List all products (filter by type/price) |
| GET | `/products/{id}` | Get product with full ingredient list |
| POST | `/products/` | Create product (auth required) |
| PUT | `/products/{id}` | Update product (owner/admin only) |
| DELETE | `/products/{id}` | Delete product (owner/admin only) |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/products/{id}/safety-score` | Ingredient safety score 0–10 |
| POST | `/products/conflict-check` | Check conflicts between products |
| GET | `/products/{id}/profile-match` | Match score for a skin type |
| GET | `/profile/recommendations` | Personalised product recommendations (JWT required) |
| GET | `/analytics/ingredient-frequency` | Top 20 most common ingredients |
| GET | `/analytics/concern-distribution` | Most common skin concerns across users |

### Skin Profile
| Method | Endpoint | Description |
|---|---|---|
| POST | `/profile/` | Create skin profile (JWT required) |
| GET | `/profile/` | Get your profile (JWT required) |
| PUT | `/profile/` | Update skin type and concerns (JWT required) |
| DELETE | `/profile/` | Delete profile (JWT required) |
| GET | `/profile/common-concerns` | Browse concerns by skin type |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/users` | List all users (admin only) |
| DELETE | `/admin/users/{id}` | Delete a user (admin only) |
| PUT | `/admin/users/{id}/make-admin` | Promote user to admin (admin only) |
| POST | `/admin/conflicts` | Create ingredient conflict pair (admin only) |
| DELETE | `/admin/conflicts/{id}` | Delete conflict pair (admin only) |

---

## MCP Server (AI Integration)

This API includes an MCP (Model Context Protocol) server that allows any MCP-compatible AI assistant to directly query the skincare database.

### Setup

1. Ensure the FastAPI server is running at `http://127.0.0.1:8000`

2. Add the following to your AI assistant's MCP config file:

```json
{
  "mcpServers": {
    "skincare-api": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/WebService_cw1/mcp_server.py"]
    }
  }
}
```

For Claude Desktop, the config file is at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. Restart your AI assistant. It will automatically discover all 8 available tools.

### Available Tools

| Tool | Description |
|---|---|
| `search_products` | Search and filter products by type or price |
| `get_product_details` | Get full ingredient list for a product |
| `check_safety_score` | Analyse ingredient safety (0–10) |
| `check_product_conflicts` | Check if products conflict |
| `get_recommendations` | Get recommendations by skin type and concern |
| `get_known_conflicts` | List all known ingredient conflict pairs |
| `profile_match` | Check how well a product matches a skin type |
| `get_ingredient_frequency` | Top 20 most common ingredients |

---

## Datasets

| Dataset | Source | Records |
|---|---|---|
| Lookfantastic Skincare Products | [Kaggle](https://www.kaggle.com) | 1,138 products |
| Celestia Skin Care Dataset | [Kaggle](https://www.kaggle.com) | 1,120 rows |
| Ingredient Conflicts | Manually curated | 12 conflict pairs |

---

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./skincare.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

For PostgreSQL (production):
```env
DATABASE_URL=postgresql://user:password@host/dbname
```

---

## Design Decisions

**Fuzzy ingredient matching** — The two datasets use inconsistent ingredient naming (e.g. `Salicylic Acid` vs `salicylic acid` vs `tea tree salicylic acid complex`). A combined contains-check and rapidfuzz similarity matching (80% threshold) solves this real data engineering problem.

**JWT stores user ID not username** — Allows users to update their username without invalidating their session token.

**Position in ProductIngredient** — Cosmetics regulations require ingredients listed in descending concentration order. Position 1 = highest concentration.

**SQLite for development, PostgreSQL for production** — SQLAlchemy's multi-dialect support means no query code changes between environments — only the `DATABASE_URL` environment variable needs updating.

**Admin role** — Separate admin endpoints for user management and conflict pair management, protected by role-based access control.