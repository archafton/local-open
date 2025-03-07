# Quickstart -

##  For first time setup see [README](../README.md)

1. Start database
```bash
brew services start postgresql
```

2. Start backend
```bash
source backend/venv/bin/activate
python3 backend/src/app.py
```

3. Start frontend
```bash
npm start
```

- Check http://localhost:3000

- Check database if no data
```bash
psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM bills;"
```