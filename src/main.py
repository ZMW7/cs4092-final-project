from customerView import CustomerView
import psycopg
import bcrypt
import sys

DB_PARAMS = {
    "dbname": "company_db",
    "host": "/tmp",
    "port": 5432
}

def hashPassword(password: str):
    # Bcrypt expects byte data, so encode the string
    password_bytes = password.encode('utf-8')
    
    # Generate a random salt (Default work factor rounds = 12)
    salt = bcrypt.gensalt()
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def authenticateCustomer():
    print("Enter username: ")
    username = input()
    print("Enter password: ")
    password = input()
    login_success = False
    # hashed_password = hashPassword(password)

    with psycopg.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            # Making sure the username and password are correct
            cur.execute("SELECT email_address, password_hash FROM customers;")

            rows = cur.fetchall()
            for row in rows:
                stored_hash = row[1]
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode("utf-8")
                
                is_valid_password = bcrypt.checkpw(password.encode("utf-8"), stored_hash)
                if username == row[0] and is_valid_password:
                    print("Customer is authenticated")
                    customer_view = CustomerView(username, conn, cur)
                    try:
                        customer_view.begin_interaction()
                    except KeyboardInterrupt:
                        customer_view.remove_all_items_from_cart()
                        conn.close()
                        cur.close()
                        sys.exit(0)
                    login_success = True
                    return
            conn.close()
        cur.close()
    if (not login_success):
        print("Invalid credentials, please try again")
    authenticateCustomer()

def getUserType():
    print("Welcome to the marketplace! Signing in as customer (y/n)")
    answer = input()
    match answer:
        case 'n' | 'N':
            print("Press 's' for seller sign-in, 'm' for moderator sign-in, or any other symbol to go back")
            nextAnswer = input()
            match nextAnswer:
                case 's':
                    pass
                case 'm':
                    pass
                case _:
                    getUserType()
                    return
        case _:
            authenticateCustomer()
            return

def main():
    getUserType()
    return

if __name__ == '__main__':
    main()