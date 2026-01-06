# Competence CRM

**A modern, unified customer relationship management platform designed for efficiency and clarity.**

## 🚀 Overview

Competence CRM streamlines client management for teams. It features a robust Python backend and a reactive modern frontend, providing real-time insights, automated status tracking, and seamless activity logging.

**Key Features:**
- **Smart Client Status**: Automatically categorizes clients as *Good*, *Due Soon*, or *Overdue* based on interaction history.
- **Role-Based Access**: Granular permissions for Admins, Managers, and Employees.
- **Data Isolation**: Employees see only their assigned clients; Managers have full team visibility.
- **Performance Analytics**: Real-time metrics on team performance and client health.

## 🛠 Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Frontend**: [React](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Authentication**: JWT (JSON Web Tokens)

## 📂 Project Structure

```
CRM/
├── api/                 # FastAPI Backend
│   ├── routers/         # API Endpoints (Auth, Clients, etc.)
│   ├── models/          # Pydantic Schemas
│   └── main.py          # Application Entry Application
├── frontend/            # React Frontend
│   ├── src/             # Components, Pages, Logic
│   └── dist/            # Built Production Assets
├── _archive/            # Legacy Code (Reference)
├── START.bat            # Unified Windows Startup Script
└── README.md            # You are here
```

## ⚡ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Setup & Run
The project includes a unified startup script for Windows.

1. **Clone the repository**
2. **Run the startup script**:
   ```powershell
   .\START.bat
   ```
   *This script will create the virtual environment, install dependencies, build the frontend, and launch the server.*

3. **Manual Setup** (If preferred):
   - **Backend**:
     ```bash
     python -m venv .venv
     .\.venv\Scripts\activate
     pip install -r requirements.txt
     python -m uvicorn api.main:app --reload --port 8001
     ```
   - **Frontend**:
     ```bash
     cd frontend
     npm install
     npm run build
     ```
   - Access the app at `http://localhost:8001`.

## 🔐 Credentials (Demo)

| Role | Email | Password |
|------|-------|----------|
| **Manager** | `manager@crm.com` | `password123` |
| **Employee** | `employee@crm.com` | `password123` |

## 🧪 Development

### Running Tests
```bash
python -m pytest api/tests
```

### Environment Variables
Create a `.env` file in the root directory:
```
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
JWT_SECRET=your_secret
```

---
*Built with ❤️ by the Competence Team.*
