# Competence CRM - Project Structure

## Overview
Employee monitoring CRM system with color theme: **White, Orange (#ff6b35), Navy Blue (#1e3a5f)**

## Folder Structure

```
backend/
├── static/
│   ├── pages/              # All dashboard pages
│   │   ├── employee-dashboard.html
│   │   ├── manager-dashboard.html
│   │   └── admin-dashboard.html
│   ├── css/
│   │   └── competence-theme.css    # Custom theme
│   ├── js/                 # JavaScript files
│   │   ├── auth.js
│   │   └── auth-check.js
│   └── adminlte/           # AdminLTE template files
├── templates/              # Jinja2 templates
│   ├── login.html
│   └── dashboard_router.html
├── models/                 # Database models
├── services/               # Business logic
├── middleware/             # Auth, audit, rate limiting
├── database/               # Schema and migrations
└── app.py                  # Main application

```

## Pages Created

### 1. Employee Dashboard (`/static/pages/employee-dashboard.html`)
- View assigned clients
- Color-coded status (Green/Orange/Red)
- Alert banner for overdue clients
- Search functionality
- Log activity button

### 2. Manager Dashboard (`/static/pages/manager-dashboard.html`)
- Team performance overview
- Employee efficiency metrics
- Client assignment interface
- Real-time monitoring

### 3. Admin Dashboard (`/static/pages/admin-dashboard.html`)
- System overview
- User statistics
- System health monitoring

## Color Theme
- **Navy Blue (#1e3a5f)**: Sidebar, primary elements
- **Orange (#ff6b35)**: Buttons, highlights, warnings
- **White (#ffffff)**: Background, cards

## Login Credentials
- Employee: john@crm.com / password123
- Manager: manager@crm.com / password123
- Admin: admin@crm.com / password123

## Start Server
```bash
cd "d:\Projects\Competence CRM\backend"
python app.py
```

Access: http://127.0.0.1:8002
