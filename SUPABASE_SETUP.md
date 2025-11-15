# Supabase Setup Instructions

## Database is Already Configured!

Your Supabase database is already set up with:
- ✅ All required tables created
- ✅ Initial users created
- ✅ Environment variables configured

## Login Credentials

**Admin Account:**
- Email: `admin@crm.com`
- Password: `admin123`

**Manager Account:**
- Email: `manager@crm.com`
- Password: `password123`

**Employee Account:**
- Email: `john@crm.com`
- Password: `password123`

## Start the Application

Simply run:
```
START.bat
```

The system will now use your Supabase database instead of demo mode.

## What Changed

1. **Demo Mode Disabled**: `USE_DEMO=0` in `.env`
2. **Real Database**: All data now persists in Supabase
3. **Production Ready**: Full authentication and data storage

## Database Tables

- `users` - User accounts (admin, manager, employee)
- `clients` - Client records with assignments
- `activity_logs` - Contact history and activities
- `daily_reports` - Employee daily work reports
- `client_assignment_history` - Assignment tracking
- `notifications` - System notifications
- `reminders` - User reminders

## Next Steps

1. Run `START.bat` to start the application
2. Login with any of the accounts above
3. Create more employees via Manager Dashboard
4. Add clients and assign them to employees
5. Employees can log activities and submit daily reports

## Troubleshooting

If you see "Database not configured" errors:
1. Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
2. Verify `USE_DEMO=0` in `.env`
3. Restart the backend: Close all Python windows and run `START.bat`
