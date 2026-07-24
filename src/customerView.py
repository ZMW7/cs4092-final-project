from psycopg import cursor, sql, Connection
from tabulate import tabulate
from collections.abc import Callable

class CustomerView:

    # Cart dict:
    # product id: [quantity]

    def __init__(self, username, conn, cur: cursor.Cursor):
        print(f"Welcome, {username}")

    def beginInteraction(self, conn, cur):
        self.showMenu(conn, cur)

    def showMenu(self, conn, cur):
        user_option_headers = ["Browse Products", "Sign Out"]
        user_options = [["p", "c"]]
        print(tabulate(user_options, user_option_headers, tablefmt = "grid"))
        user_input = input()
        self._cart = dict()
        should_continue = True
        while (should_continue):
            match user_input:
                case 'p' | 'P':
                    should_continue = self.listProducts(conn, cur)
                case _:
                    pass

    def removeAllItemsFromCart(self, conn: Connection, cur: cursor.Cursor):
        print("\nRemoving all items from cart...")
        query = ""
        items_list = list(self._cart.items())
        cur.executemany(
            "UPDATE products SET stock = stock + %s WHERE id = %s",
            items_list
        )
        conn.commit()

    def addToCart(self, conn: Connection, cur: cursor.Cursor, previous_page: Callable[[cursor.Cursor], None]):
        try:
            product_id = input("Enter the product ID of the product to add: ")
            quantity = int(input("quantity: "))

            query = sql.SQL("SELECT product_name, stock, price FROM products WHERE id = %s")
            cur.execute(query, (product_id,))

            # If the product ID is invalid, notify user and return to previous page
            product_rows = cur.fetchall()
            if (len(product_rows) != 1):
                print("Invalid product ID")
                previous_page(conn, cur)

            name, stock, price = product_rows[0]
            print(f"Name: {name}, stock: {stock}, price: {price}\n ")
            # If the quantity is invalid, try again
            if (quantity > stock):
                print(f"Requested quantity ({quantity}) exceeds current stock ({stock}), please try again")
                previous_page(conn, cur)

            # Adding to cart
            update_query_str = """
                UPDATE products
                SET stock = stock - %s
                WHERE id = %s;
            """
                
            cur.execute(update_query_str, (quantity, product_id))
            conn.commit()

            # Updating cart
            self._cart[product_id] = quantity

        except ValueError:
            print("Invalid input, please try again.")
            previous_page(conn, cur)
        

    def listProducts(self, conn, cur: cursor.Cursor):
        # Getting the products
        query = """
            SELECT p.id, p.product_name, p.stock, s.seller_name, p.price
            FROM products as p
            JOIN sellers as s ON p.seller_id = s.id;
        """
        cur.execute(query)
        product_rows = cur.fetchall()
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
                self.addToCart(conn, cur, self.listProducts)
            case 's' | 'S':
                # Remove from Cart
                return False
            case 'd' | 'D':
                # Rate
                return False
            case 'r' | 'R':
                return False
            
        return True