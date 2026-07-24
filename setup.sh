DB_NAME="company_db"

psql -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

# Setting up the sample data
psql -d postgres -f src/setup.sql

# Running the demo
psql -d company_db -f src/demo.sql