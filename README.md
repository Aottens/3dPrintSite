# NovaPrint Platform

NovaPrint is a reference implementation of a 3D printing service built from the PRD v1.0 specification. It includes a FastAPI backend that exposes quoting and order management endpoints and a Next.js/TailwindCSS frontend that demonstrates the customer and admin portals described in the requirements.

## Project structure

```
.
├── backend/              # FastAPI application implementing API endpoints
│   └── app/
│       ├── config.py     # Default pricing coefficients and versioning model
│       ├── main.py       # REST API with upload, quote, order, and admin routes
│       └── pricing.py    # Pricing calculation utilities
├── frontend/             # Next.js 14 application with TailwindCSS styling
│   ├── app/              # App Router pages and layout
│   ├── components/       # Customer and admin UI building blocks
│   ├── lib/              # API client helpers
│   └── styles/           # Tailwind global styles
└── docs/
    └── PRD.md            # Full product requirements document (v1.0)
```

## Getting started

### Backend (FastAPI)

1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. The API will be available at `http://localhost:8000`. The OpenAPI schema lives at `/docs`.

### Frontend (Next.js)

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Visit `http://localhost:3000` to interact with the portal. Set `NEXT_PUBLIC_API_URL` to point to the FastAPI service if it differs from the default `http://localhost:8000`.

## Implemented features

- Instant quoting backed by the default coefficients from the PRD, including material, machine, base, post-processing, and risk multipliers.
- Pricing configuration endpoint with versioning support and a corresponding admin panel view.
- Material catalogue management with a REST endpoint and UI table.
- Order creation, retrieval, and status updates with simple in-memory persistence.
- Customer portal experiences for upload & quote, cart & checkout, and account dashboard.
- Admin portal views for analytics, pricing management, orders, and user administration mockups.

## Next steps

- Replace in-memory storage with PostgreSQL using SQLModel or SQLAlchemy.
- Integrate a real STL processing microservice (e.g. trimesh) to compute volume and surface area from uploaded models.
- Connect to Stripe or Mollie for payments and configure transactional email notifications.
- Harden authentication with JWT and role-based access control.
- Add automated tests covering pricing calculations and API workflows.
