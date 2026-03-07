# WebService_cw1

models/      → defines what your database tables look like
              "A Product has a name, brand, price, rating..."

schemas/     → defines what JSON going in and out looks like
              "When creating a product, I expect name + brand + price"
              "When returning a product, I send back id + name + brand..."

routers/     → the actual endpoints
              "When someone hits GET /products/, do this..."

core/        → shared tools used everywhere
              "Here's how to hash a password"
              "Here's how to verify a token"

data/        → one-time scripts
              "Read the CSV and dump it into the database"


This week (before 13 March deadline):
1. ✅ Finish project structure (you're here)
2. ⬜ Write your models.py
3. ⬜ Find and download skincare dataset from Kaggle
4. ⬜ Write import script
5. ⬜ Build CRUD endpoints
6. ⬜ Build analytics endpoints
7. ⬜ Add authentication
8. ⬜ Build simple frontend
9. ⬜ Export Swagger as PDF
10. ⬜ Write technical report
11. ⬜ Make slides
12. ⬜ Make repo public

┌─────────────────────┐
│      products       │
├─────────────────────┤
│ id                  │
│ name                │
│ brand               │
│ price               │
│ rating              │
│ size                │
│ loves_count         │
└──────────┬──────────┘
           │
           │ one product, many ingredients
           │
┌──────────▼──────────┐
│  product_ingredients│
├─────────────────────┤        ┌─────────────────────┐
│ id                  │        │     ingredients     │
│ product_id    ──────┼──┐     ├─────────────────────┤
│ ingredient_id ──────┼──┼────►│ id                  │
│ position            │  │     │ name                │
└─────────────────────┘  │     │ irritation_level    │
                         │     └──────────┬──────────┘
                         │                │
                         │                │ one ingredient
                         │                │ recommended for
                         │                │ many concerns
                         │     ┌──────────▼──────────┐
                         │     │  concern_ingredients │
                         │     ├─────────────────────┤
                         │     │ concern_id           │
                         │     │ ingredient_id  ◄─────┘
                         │     └──────────┬──────────┘
                         │                │
                         │     ┌──────────▼──────────┐
                         │     │    skin_concerns     │
                         │     ├─────────────────────┤
                         │     │ id                  │
                         │     │ name                │
                         │     └─────────────────────┘
                         │
           ┌─────────────▼──────────────┐
           │    ingredient_conflicts    │
           ├────────────────────────────┤
           │ id                         │
           │ ingredient_1_id            │
           │ ingredient_2_id            │
           │ severity                   │
           │ reason                     │
           │ recommendation             │
           └────────────────────────────┘

┌─────────────────────┐         ┌─────────────────────┐
│       users         │         │    user_profiles    │
├─────────────────────┤         ├─────────────────────┤
│ id                  │◄────────│ user_id             │
│ username            │         │ skin_concern_id     │
│ email               │         │ age_range           │
│ hashed_password     │         │ budget              │
│ is_active           │         └─────────────────────┘
└─────────────────────┘