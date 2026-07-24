import psycopg
from tabulate import tabulate

def listProducts(cursor: psycopg.cursor):
    # Getting the products
    query = """
        SELECT p.id, p.product_name, p.stock, s.seller_name, p.price
        FROM products as p
        JOIN sellers as s ON p.seller_id = s.id;
    """
    cursor.execute(query)
    product_rows = cursor.fetchall()
    print("Products:")
    print(tabulate(product_rows, headers = ["ID", "Name", "Stock", "Seller", "Price"], tablefmt="grid"))

    # Presenting customer options   
    user_options = [
        ["Add to Cart", "Remove from Cart", "Rate", "Report"],
        ["a", "s", "d", "f"]
    ]
    print("Controls: ")
    print(tabulate([user_options[1]], user_options[0], tablefmt = "simple"))

    # Getting the user input
    user_input = input()
    match user_input:
        case 'a' | 'A':
            # Add to cart
            pass
        case 's' | 'S':
            # Remove from Cart
            pass
        case 'd' | 'D':
            # Rate
            pass
        case 'r' | 'R':
            pass

class CustomerView:

    def __init__(self, username, cursor: psycopg.cursor):
        print(f"Welcome, {username}")
        user_option_headers = ["Browse Products", "Sign Out"]
        user_options = [["p", "c"]]
        print(tabulate(user_options, user_option_headers, tablefmt = "grid"))
        user_input = input()
        match user_input:
            case 'p' | 'P':
                listProducts(cursor)
            case _:
                pass