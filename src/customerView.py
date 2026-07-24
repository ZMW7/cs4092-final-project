from psycopg import cursor, sql, Connection
from tabulate import tabulate
from collections.abc import Callable

class CustomerView:

    # Cart dict:
    # product id: [quantity]

    def __init__(self, username, conn, cur: cursor.Cursor):
        print(f"Welcome, {username}")

    def beginInteraction(self, conn, cur):
        self._cart = dict()
        self.showMenu(conn, cur)

    def showMenu(self, conn, cur):
        user_option_headers = ["Browse Products", "Sign Out"]
        user_options = [["p", "c"]]
        should_continue = True
        while (should_continue):
            print(tabulate(user_options, user_option_headers, tablefmt = "grid"))
            user_input = input()
            match user_input:
                case 'p' | 'P':
                    should_continue = self.listProducts(conn, cur)
                case 'c' | 'C':
                    break
                case _:
                    pass
        self.removeAllItemsFromCart(conn, cur)
        print("See ya! 👋")

    def removeAllItemsFromCart(self, conn: Connection, cur: cursor.Cursor):
        print("\nRemoving all items from cart...")
        query = ""
        items_list = list(self._cart.items())
        cur.executemany(
            "UPDATE products SET stock = stock + %s WHERE id = %s",
            items_list
        )
        conn.commit()

    def displayRemoveFromCartOptions(self, conn: Connection, cur: cursor.Cursor, previous_page: Callable):
        try:
            print("\nRemoving items from cart")
            self.displayCurrentCart(conn, cur)

            product_id = (int)(input("Enter the product ID of the product to remove from your cart: "))
            quantity_str = input("quantity to remove (leave blank for all): ")
            quantity = 0
            query = sql.SQL("SELECT product_name, stock FROM products WHERE id = %s")
            cur.execute(query, (product_id,))

            # If the product does not exist, notify the user and return to the previous page
            product_rows = cur.fetchall()
            if (len(product_rows) < 1):
                print("Invalid product ID, please try again.")
                return previous_page

            if not (product_id in self._cart.keys()):
                print(f"Product ID {product_id} is not in cart, please try again.")
                print(f"current cart: {self._cart.items()}")
                return previous_page

            product_name, stock = product_rows[0]

            if (quantity_str == ""):
                quantity = self._cart[product_id]
            else:
                quantity = min(int(quantity_str), self._cart[product_id])

            # If the quantity is 0, no need to continue any further.
            if (quantity == 0):
                print("Successfully removed 0 items from cart.")
                return

            # Removing from cart
            self._cart[product_id] -= quantity

            # If the quantity is 0, the item should be removed
            if (self._cart[product_id] == 0):
                self._cart.pop(product_id)

            # Updating stock in database
            update_query_str = """
                UPDATE products
                SET stock = stock + %s
                WHERE id = %s
            """

            cur.execute(update_query_str, (quantity, product_id,))
            conn.commit()
            return previous_page
            
        except ValueError:
            print("Invalid input, please try again")
            return previous_page

    def displayAddToCartOptions(self, conn: Connection, cur: cursor.Cursor, previous_page: Callable[[cursor.Cursor], None]):
        try:
            product_id = int(input("Enter the product ID of the product to add: "))
            quantity = int(input("quantity: "))

            query = sql.SQL("SELECT product_name, stock, price FROM products WHERE id = %s")
            cur.execute(query, (product_id,))

            # If the product ID is invalid, notify user and return to previous page
            product_rows = cur.fetchall()
            if (len(product_rows) != 1):
                print("Invalid product ID")
                return previous_page

            name, stock, price = product_rows[0]
            print(f"Name: {name}, stock: {stock}, price: {price}\n ")
            # If the quantity is invalid, try again
            if (quantity > stock):
                print(f"Requested quantity ({quantity}) exceeds current stock ({stock}), please try again")
                return previous_page

            # Adding to cart
            update_query_str = """
                UPDATE products
                SET stock = stock - %s
                WHERE id = %s
            """
                
            cur.execute(update_query_str, (quantity, product_id,))
            conn.commit()

            # Updating cart
            if (product_id in self._cart.keys()):
                self._cart[product_id] += quantity
            else:
                self._cart[product_id] = quantity
            return previous_page

        except ValueError:
            print("Invalid input, please try again.")
            return previous_page

    def displayCurrentCart(self, conn: Connection, cur: cursor.Cursor):
        print("Current cart: ")
        table_headings = ["Product ID", "Product Name", "Count"]

        # Constructing the query
        if (len(self._cart.items()) == 0):
            print("Cart is empty")
            return
        
        product_names_query = """
            SELECT id, product_name FROM products WHERE id IN (
        """
        number_of_items_in_cart = len(self._cart.keys())
        for index, key in enumerate(self._cart.keys()):
            product_names_query += str(key)
            if (index < number_of_items_in_cart - 1):
                product_names_query += ", "
        product_names_query += ")"

        # Executing the query
        cur.execute(product_names_query)
        product_rows = cur.fetchall()
        table_contents = list()
        for row in product_rows:
            product_id = row[0]
            product_name = row[1]
            table_contents.append([product_id, product_name, self._cart[product_id]])

        print(tabulate(table_contents, headers=table_headings, tablefmt="grid"))

        # Showing the next options
        return
        

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
            ["Add to Cart", "Remove from Cart", "Rate", "Report", "View Cart"],
            ["a", "s", "d", "f", "v"]
        ]
        print("Controls: ")
        print(tabulate([user_options[1]], user_options[0], tablefmt = "simple"))

        # Getting the user input
        user_input = input()
        match user_input:
            case 'a' | 'A':
                # Add to cart
                next_page = self.displayAddToCartOptions(conn, cur, self.listProducts)
                next_page(conn, cur)
            case 's' | 'S':
                # Remove from Cart
                next_page = self.displayRemoveFromCartOptions(conn, cur, self.listProducts)
                next_page(conn, cur)
            case 'd' | 'D':
                # Rate
                return False
            case 'r' | 'R':
                return False
            case 'v' | 'V':
                self.displayCurrentCart(conn, cur)
                return True
            
        return True