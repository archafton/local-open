
# 1st Terminal
cd backend
source venv/bin/activate
python3 src/api.py

# 2nd Terminal
npm start

# 3rd Terminal
check database
    psql postgresql://localhost/project_tacitus_test -c "SELECT COUNT(*) FROM bills;"

cd backend
source venv/bin/activate

python3 src/python/congressgov/bill_fetch/bill_fetch.py

