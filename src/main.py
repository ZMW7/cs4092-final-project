from customerView import CustomerView
import psycopg
import bcrypt
import sys
import re # regex

DB_PARAMS = {
    "dbname": "company_db",
    "host": "/tmp",
    "port": 5432
}

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
MAX_EMAIL_LENGTH = 320 # according to RFC-5321

def hashPassword(password: str):
    # Bcrypt expects byte data, so the string must be encoded
    password_bytes = password.encode('utf-8')
    
    # Generate a random salt (Default work factor rounds = 12)
    salt = bcrypt.gensalt()
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def is_valid_email(email: str) -> bool:
    if (not email or len(email) > MAX_EMAIL_LENGTH):
        return False
    else:
        return bool(re.match(EMAIL_REGEX, email))

def create_customer_account():
    with psycopg.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            account_successfully_created: bool = False
            while not (account_successfully_created):
                email_address: str | None = None
                while not (is_valid_email(email_address)):
                    email_address = input("Email address: ")
                    if not is_valid_email(email_address):
                        print("Invalid email address.")
                password: str | None = None
                while (password == None or len(password) < 3):
                    password = input("Password: ")
                    if (len(password) < 3):
                        print("Password must be at least three characters. Please try again.")
                password_hash = hashPassword(password=password)

                # Adding the user to the database
                try:
                    print(f"password_hash: {password_hash} ({len(password_hash.decode())} characters)")
                    cur.execute("INSERT INTO customers (email_address, password_hash) VALUES (%s, %s) RETURNING id", (email_address, password_hash.decode(),))
                    conn.commit()
                    result_rows = cur.fetchall()
                    if (len(result_rows) != 1):
                        print("Something went wrong.")
                        continue
                    customer_id = result_rows[0][0]
                    customer_view = CustomerView(email_address, conn, cur)
                    try:
                        customer_view.begin_interaction()
                    except KeyboardInterrupt:
                        customer_view.remove_all_items_from_cart()
                        print("See ya! 👋")
                        conn.close()
                        cur.close()
                        sys.exit(0)
                except psycopg.errors.UniqueViolation:
                    print("Email address already exists. Please try again.")
                    continue

def authenticateCustomer():
    user_response = input("Enter 'login' or press enter to login. Enter 'signup' to create an account! ")
    match user_response:
        case 'signup':
            create_customer_account()
            return
        case 'login' | '' | _:
            pass

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
                        print("See ya! 👋")
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