# Database Management Guide for Project Tacitus

This guide provides comprehensive instructions for managing PostgreSQL databases for the Project Tacitus application. It covers creating, initializing, switching between, and maintaining databases for development and testing purposes.

## 1. Creating New Databases

### Prerequisites

- PostgreSQL installed and running
- Basic knowledge of PostgreSQL commands
- Access to the project repository

### Creating a New Database

To create a new database for Project Tacitus, use the `createdb` command:

```bash
createdb project_tacitus_dev
```

You can replace `project_tacitus_dev` with any name that follows your naming convention, such as:
- `project_tacitus_test` - For testing environments
- `project_tacitus_dev` - For development work
- `project_tacitus_prod` - For production (if applicable)

### Verifying Database Creation

To verify that your database was created successfully:

```bash
psql -l
```

This will list all available databases. Your newly created database should appear in the list.

## 2. Database Initialization

After creating a new database, you need to initialize it with the project schema.

### Running the Schema Script

Execute the schema SQL script to create all necessary tables, indexes, and initial data:

```bash
psql -d project_tacitus_dev -f backend/src/schema.sql
```

### Understanding the Initialization Output

When running the schema script on a new database, you'll see output similar to:

```
ERROR: relation "members" does not exist
ERROR: relation "bill_cosponsors" does not exist
...
CREATE TABLE
CREATE TABLE
...
ALTER TABLE
...
CREATE INDEX
...
```

**Note:** The initial errors are expected and not problematic. They occur because the script attempts to drop existing tables before creating new ones. Since this is a fresh database, those tables don't exist yet.

### Verifying Initialization

To verify that your database was initialized correctly:

```bash
psql -d project_tacitus_dev -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

This should return a count of the tables created in your database.

## 3. Switching Between Databases

Project Tacitus uses the `DATABASE_URL` environment variable to determine which database to connect to. There are several ways to switch between databases.

### Method 1: Modifying the .env File

The simplest approach is to edit the `.env` file in the backend directory:

1. Open `backend/.env`
2. Modify the `DATABASE_URL` line:

```
# For test database
DATABASE_URL=postgresql://localhost/project_tacitus_test

# For development database (uncomment when needed)
# DATABASE_URL=postgresql://localhost/project_tacitus_dev
```

After changing the `.env` file, restart the application for changes to take effect.

### Method 2: Using Environment Variables

You can override the database connection without modifying the `.env` file by setting the environment variable when starting the application:

```bash
# For test database (uses .env default)
cd backend && python src/app.py

# For development database
cd backend && DATABASE_URL=postgresql://localhost/project_tacitus_dev python src/app.py
```

### Method 3: Setting Environment Variables in Virtual Environment

If you're using a virtual environment, you can set the environment variable for the duration of your session:

```bash
# Activate your virtual environment
source backend/venv/bin/activate

# Set the database URL
export DATABASE_URL=postgresql://localhost/project_tacitus_dev

# Now run the application (it will use the exported variable)
cd backend && python src/app.py
```

To make this persistent in your virtual environment, you can add the export command to the activation script:

```bash
echo 'export DATABASE_URL=postgresql://localhost/project_tacitus_dev' >> backend/venv/bin/activate
```

### Method 4: Creating Convenience Scripts

For easier switching, create shell scripts:

**run_test.sh**:
```bash
#!/bin/bash
cd backend
DATABASE_URL=postgresql://localhost/project_tacitus_test python src/app.py
```

**run_dev.sh**:
```bash
#!/bin/bash
cd backend
DATABASE_URL=postgresql://localhost/project_tacitus_dev python src/app.py
```

Make the scripts executable:
```bash
chmod +x run_test.sh run_dev.sh
```

## 4. Database Maintenance

### Wiping/Cleaning a Database

There are several approaches to wiping or cleaning a database:

#### Option 1: Drop and Recreate

This is the most thorough approach:

```bash
dropdb project_tacitus_dev
createdb project_tacitus_dev
psql -d project_tacitus_dev -f backend/src/schema.sql
```

#### Option 2: Truncate All Tables

To keep the structure but remove all data:

```bash
psql -d project_tacitus_dev -c "
DO
\$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE;';
    END LOOP;
END
\$\$;
"
```

#### Option 3: Reset Specific Tables

To selectively clean tables:

```bash
psql -d project_tacitus_dev -c "TRUNCATE TABLE bills, members CASCADE;"
```

### Backing Up a Database

To create a backup:

```bash
pg_dump -Fc project_tacitus_dev > tacitus_dev_backup.dump
```

### Restoring from Backup

To restore from a backup:

```bash
# For an existing database
pg_restore -d project_tacitus_dev tacitus_dev_backup.dump

# Or to create a new database from the backup
createdb project_tacitus_new
pg_restore -d project_tacitus_new tacitus_dev_backup.dump
```

## 5. Best Practices

### Database Naming Conventions

- Use clear, consistent naming: `project_tacitus_<environment>`
- Avoid spaces or special characters in database names

### Development vs. Test Databases

- **Test Database**: Used for automated tests, should be regularly reset to a known state
- **Development Database**: Used for active development, may contain more experimental data

### Database Version Control

- Keep track of schema changes in version control
- Use migration scripts for schema updates
- Document major schema changes

### Security Considerations

- Don't use the same passwords for development and production
- Avoid committing database credentials to version control
- Use environment variables for sensitive configuration

## 6. Troubleshooting

### Common Issues

#### Connection Refused

If you see "connection refused" errors:
- Ensure PostgreSQL is running: `pg_ctl status`
- Check if you can connect manually: `psql -d project_tacitus_dev`

#### Permission Denied

If you encounter permission issues:
- Ensure your user has the necessary permissions
- Try connecting as the postgres user: `sudo -u postgres psql`

#### Schema Errors

If schema initialization fails:
- Check for syntax errors in schema.sql
- Ensure you're running the command from the project root directory

## 7. Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- Project Tacitus internal documentation in the `Docs` directory
