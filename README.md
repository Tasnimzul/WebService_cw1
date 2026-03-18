# WebService_cw1

# Skincare & Ingredient Analysis API

A data-driven RESTful API for skincare product recommendations, ingredient safety analysis, and conflict detection. Built with FastAPI and backed by real product data from Lookfantastic (1,138 products) and a dermatological skin concern dataset.

**Module:** COMP3011 Web Services — University of Leeds  
**Student:** Tasnim Zulkifli  
**GitHub:** https://github.com/Tasnimzul/WebService_cw1

---

## Features

- Browse and search more than 1000 real skincare products
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

## Usage

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Frontend application |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc documentation |

### API Documentation

Full API documentation is available in [API_documentation.pdf](./API_documentation.pdf)

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
| GET | `/profile/recommendations` | Personalised product recommendations |
| GET | `/analytics/ingredient-frequency` | Top 20 most common ingredients |
| GET | `/analytics/concern-distribution` | Most common skin concerns across users |

### Skin Profile
| Method | Endpoint | Description |
|---|---|---|
| POST | `/profile/` | Create skin profile |
| GET | `/profile/` | Get your profile |
| PUT | `/profile/` | Update skin type and concerns |
| DELETE | `/profile/` | Delete profile |
| GET | `/profile/common-concerns` | Browse concerns by skin type |

---

## MCP Server (AI Integration)

This API includes an MCP (Model Context Protocol) server that allows AI assistants like Claude to directly query the skincare database.

### Setup with Claude Desktop

1. Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

2. Start the FastAPI server, then restart Claude Desktop.

3. Claude can now call your API directly:
   - *"Check if products 1 and 5 have ingredient conflicts"*
   - *"What products are recommended for oily skin with acne?"*
   - *"What is the safety score of product 3?"*

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

---

## Design Decisions

**Fuzzy ingredient matching** — The two datasets use inconsistent ingredient naming (e.g. `Salicylic Acid` vs `salicylic acid` vs `tea tree salicylic acid complex`). A combined contains-check and rapidfuzz similarity matching (80% threshold) solves this real data engineering problem.

**JWT stores user ID not username** — Allows users to update their username without invalidating their session token.

**Position in ProductIngredient** — Cosmetics regulations require ingredients listed in descending concentration order. Position 1 = highest concentration.

**Admin role** — Separate admin endpoints for user management and conflict pair management, protected by role-based access control.