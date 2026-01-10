# NovaPrint Platform

NovaPrint is a complete 3D printing service platform with a FastAPI backend, Next.js frontend, and PostgreSQL database. It provides instant quoting, order management, and an admin portal for managing materials, pricing, and orders.

## Quick Start (One Command)

The easiest way to run NovaPrint is with Docker. This starts all services (database, backend, frontend) with a single command.

### Prerequisites

You need to install Docker Desktop on your computer:

1. **Windows**: Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. **Mac**: Download and install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
3. **Linux**: Follow the [Docker Engine installation guide](https://docs.docker.com/engine/install/)

### Running NovaPrint

1. Open a terminal (Command Prompt, PowerShell, or Terminal)
2. Navigate to the project folder:
   ```bash
   cd path/to/3dPrintSite
   ```
3. Start everything with Docker Compose:
   ```bash
   docker compose up
   ```
4. Wait for all services to start (this may take a few minutes the first time)
5. Open your browser and go to:
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs

### Default Accounts

After startup, you can log in with these test accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@novaprint.local | admin123 |
| Customer | demo@example.com | demo123 |

### Stopping NovaPrint

Press `Ctrl+C` in the terminal, or run:
```bash
docker compose down
```

## Project Structure

```
.
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Settings, security, dependencies
│   │   ├── db/             # Database models and seed data
│   │   └── services/       # Business logic (pricing, storage, metrics)
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests (pytest)
├── frontend/               # Next.js React frontend
│   ├── app/                # Pages and layouts
│   ├── components/         # UI components
│   └── lib/                # API client and state management
├── e2e/                    # End-to-end tests (Playwright)
├── docker-compose.yml      # Docker services configuration
└── .github/workflows/      # CI/CD pipeline
```

## Features

### Customer Portal
- Upload STL/3MF files with automatic validation
- 3D model preview in the browser
- Automatic calculation of model metrics (volume, surface area, dimensions)
- Select technology (FDM/Resin), material, color, and print profile
- Instant price quotes with detailed breakdown
- Shopping cart and order placement
- Order history and status tracking

### Admin Portal
- Dashboard with analytics (orders, revenue)
- Materials management (add, edit, delete materials and colors)
- Print profiles management
- Pricing rule sets with version control
- Orders management with status updates
- Manual price override with audit logging
- User management

### Technical Features
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations for database schema changes
- JWT authentication with role-based access control
- File upload with STL/3MF validation via trimesh
- Versioned pricing rules with snapshot storage
- Docker Compose for easy deployment
- CI/CD with GitHub Actions
- Unit, integration, and end-to-end tests

## Development Setup

If you want to run the services individually for development:

### Backend

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Mac/Linux
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (create `.env` file):
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/novaprint
   JWT_SECRET=your-secret-key-here
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Seed the database:
   ```bash
   python -m app.db.seed
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Set up environment variables (create `.env.local` file):
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at http://localhost:3000

## Running Tests

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### End-to-End Tests
```bash
# Start the application first, then:
cd e2e
npm install
npx playwright install
npm test
```

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET` | Secret key for JWT tokens | Required |
| `UPLOAD_DIR` | Directory for uploaded files | `./uploads` |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size | `200` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## API Documentation

When the backend is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Troubleshooting

### Docker issues

**"Cannot connect to Docker daemon"**
- Make sure Docker Desktop is running

**"Port already in use"**
- Stop other services using ports 3000, 8000, or 5432
- Or modify the ports in `docker-compose.yml`

**"Database connection failed"**
- Wait a few seconds for PostgreSQL to fully start
- Check that the database container is running: `docker compose ps`

### Development issues

**"Module not found" errors in backend**
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

**"Cannot find module" errors in frontend**
- Run `npm install` again
- Delete `node_modules` and `package-lock.json`, then run `npm install`

**"CORS error" in browser**
- Make sure `NEXT_PUBLIC_API_URL` matches the backend URL
- Check that the backend is running

## License

This project is for educational and demonstration purposes.
