from psycopg import cursor, sql, Connection
from tabulate import tabulate
from collections.abc import Callable
from decimal import Decimal
from typing import NamedTuple
from datetime import datetime as datetime, date as dtdate
import itertools
import textwrap
import readline # for up arrow support on linux / mac
import enum

from commonTypes import AddressEntry, PaymentMethodEntry, PurchaseEntry, ProductSalesEntry, DeliveryEntry, RatingEntry, ReportReason, ReportEntry, PurchaseHistoryEntry

def strict_truncate_str(text: str, max_length: int = 15):
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

class CustomerView:

    # Cart dict:
    # product id: [quantity]

    def __init__(self, username, conn: Connection, cur: cursor.Cursor):
        self.conn = conn
        self.cur = cur
        print(f"Welcome, {username}")
        self._username = username
        # Getting the customer ID
        customer_id_query = sql.SQL("SELECT id FROM customers WHERE email_address = %s")
        cur.execute(customer_id_query, (username,))
        customer_rows = cur.fetchall()
        if (len(customer_rows) != 1):
            raise ValueError(f"Error: customer id has {len(customer_rows)} matches, expected 1.")
        self._customer_id = customer_rows[0][0]

    def begin_interaction(self):
        self._cart = dict()
        self.show_menu()

    def show_menu(self):
        user_option_headers = ["Browse Products", "Checkout", "My Purchases", "Sign Out"]
        user_options = [["p", "c", "h", "x"]]
        should_continue = True
        while (should_continue):
            print(tabulate(user_options, user_option_headers, tablefmt = "fancy_grid"))
            user_input = input()
            match user_input:
                case 'p' | 'P':
                    # Browse products
                    should_continue = self.list_products()
                case 'c' | 'C':
                    # Checkout
                    should_continue = self.display_checkout_options()
                case 'h' | 'H':
                    # My purchases
                    should_continue = self.display_purchase_history(0)
                case 'x' | 'X':
                    should_continue = False
                case _:
                    pass
        if (len(self._cart.items()) > 0):
            self.remove_all_items_from_cart()
        print("See ya! 👋")

    def remove_all_items_from_cart(self):
        print("\nRemoving all items from cart...")
        items_list = [(quantity, product_id) for product_id, quantity in self._cart.items()]
        self.cur.executemany(
            "UPDATE products SET stock = stock + %s WHERE id = %s",
            items_list
        )
        self.conn.commit()
        self._cart.clear()

    def display_new_address_input_options_and_add_to_database(self) -> AddressEntry:
        print("\nNew Address")

        country = input("Country: ")
        administrative_division = input("Administrative division (e.g. state, province): ")
        city = input("City: ")
        line1 = input("Address line 1: ")
        line2 = input("Address line 2 (optional): ")
        postal_code = input("Postal code: ")

        # Ensuring input validity
        while (len(country) < 1 or len(country) > 56):
            print("Invalid country, please retry.")
            country = input("Country: ")
        while (len(administrative_division) > 24):
            print("Invalid administrative division (must be less than 24 characters), please retry.")
            administrative_division = input("Administrative division (e.g. state, province): ")
        while (len(city) < 1 or len(city) > 127):
            print("Invalid city, please retry.")
            city = input("City: ")
        while (len(line1) < 1 or len(line1) > 127):
            print("Invalid address line 1, please retry.")
            line1 = input("Address line 1: ")
        while (len(line2) > 127):
            print("Invalid address line 2, please retry.")
            line2 = input("Address line 2: ")
        while (len(postal_code) < 1 or len(postal_code) > 10):
            print("Invalid postal code, please retry.")
            postal_code = input("Postal code: ")

        # Ensuring null values are null
        if (len(administrative_division) == 0):
            administrative_division = None
        if (len(line2) == 0):
            line2 = None

        # Adding new address to database
        self.cur.execute(
            """
                INSERT INTO addresses (country, administrative_division, city, line1, line2, postal_code, customer_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
            (country, administrative_division, city, line1, line2, postal_code, self._customer_id)
        )
        self.conn.commit()

        # Getting the address ID of the new address
        rows = self.cur.fetchall()
        if (len(rows) != 1):
            raise ValueError(f"Expected 1 row, got {len(rows)}")
        address_id = rows[0][0]

        user_response = input(f"Would you like to make {line1} your preferred address? (y/n, blank is y): ")
        match user_response:
            case 'y' | 'Y' | '':
                print("Updating preferred address...", end='\r', flush=True)
                self.cur.execute(
                    """
                    UPDATE customers
                    SET primary_address_id = %s
                    WHERE id = %s
                    """,
                    (address_id, self._customer_id,)
                )
                self.conn.commit()
                print("Preferred address updated!   ")

        return AddressEntry(
            id=address_id,
            country=country,
            administrative_division=administrative_division,
            city=city,
            line1=line1,
            line2=line2,
            postal_code=postal_code,
            customer_id=self._customer_id
        )

    def prompt_user_to_select_address(self) -> AddressEntry:
        print("\nRetreiving addresses...", end='\r', flush=True)
        # Retreiving payment methods
        self.cur.execute(
            "SELECT * FROM addresses WHERE customer_id = %s",
            (self._customer_id,)
        )
        print("Addresses              ")
        address_rows = self.cur.fetchall()
        address_options = list()
        address = None
        if (len(address_rows) > 0):
            # There are existing addresses, and the customer should be able to select from these
            for index, address_row in enumerate(address_rows):
                address_options.append([index + 1, address_row[4]])
        address_options.append([len(address_rows) + 1, 'New address'])

        # Printing table of addresses
        print(tabulate(address_options, headers=['No.', 'Address'], tablefmt='fancy_grid'))

        # Updating the address
        selection_number = len(address_rows) + 2
        new_address_selection_number = len(address_rows) + 1
        while not (0 < selection_number < len(address_rows) + 2):
            try:
                selection_number = int(input("Please select an address (by number): "))
                if not (0 < selection_number < len(address_rows) + 2):
                    print("Invalid selection.", end=" ")
            except ValueError:
                print("Invalid selection.", end=" ")

        if (new_address_selection_number == selection_number):
            address = self.display_new_address_input_options_and_add_to_database()
        else:
            address = AddressEntry(
                id=address_rows[selection_number-1][0],
                country=address_rows[selection_number-1][1],
                administrative_division=address_rows[selection_number-1][2],
                city=address_rows[selection_number-1][3],
                line1=address_rows[selection_number-1][4],
                line2=address_rows[selection_number-1][5],
                postal_code=address_rows[selection_number-1][6],
                customer_id=address_rows[selection_number-1][7]
            )
        return address

    def update_preferred_payment_method(self, payment_id: int):
        print(f"Updating preferred payment method to id {payment_id}")
        self.cur.execute("""
            UPDATE customers
            SET preferred_payment_id = %s
            WHERE id = %s
        """,
        (payment_id, self._customer_id,))
        self.conn.commit()


    def display_new_payment_method_input_options_and_add_payment_method(self, billing_address: AddressEntry = None) -> PaymentMethodEntry:
        """
        Prompts the user to enter information for a new payment method 
        and adds the newly created payment method to the database.

        Parameters
        -------
        billing_address: AddressEntry | None
            The billing address of the payment method
        
        Returns
        ------- 
        int
            The ID of the newly created payment method.
        """

        print("\nEnter payment information")

        # Card number
        user_response = input("Card number: ")
        card_number = "".join([character for character in user_response if character.isdigit()])
        while not (8 < len(card_number) < 20):
            card_number = input("Invalid card number. Please re-enter card number: ")

        # Card expiration
        card_expiration = None
        while (card_expiration == None):
            try:
                card_expiration_str = input("Expiration: ")
                card_expiration = datetime.strptime(card_expiration_str, "%m/%y")
            except:
                print("Invalid expiration. Expiration should be in 'month/year' format.", end=" ")
                card_expiration = None

        # Card code
        card_code = None
        while (card_code == None):
            card_code = (input("Card code (those three or four magic numbers on the back): "))
            try:
                temp = int(card_code)
            except ValueError:
                print("Invalid card code. Card code must be three or four digits.", end=" ")
                card_code = None
                continue
            if not (len(card_code) == 3 or len(card_code) == 4):
                card_code = None

        # Giving the user the option to use their current billing address, or create a new one
        if (billing_address != None):
            user_response = input(f"Would you like to use {billing_address.line1} as your billing address? (y/n, blank is y)")
            match user_response:
                case 'y' | 'Y' | "":
                    pass
                case _:
                    billing_address = None
                    pass
        if (billing_address == None):
            billing_address = self.prompt_user_to_select_address()

        # Adding the newly created payment method to the database
        self.cur.execute("""
            INSERT INTO payment_methods (card_number, card_expiration, card_code, billing_address_id, customer_id) VALUES
            (%s, %s, %s, %s, %s)
            RETURNING id
        """,
        (card_number, card_expiration, card_code, billing_address.id, self._customer_id,)
        )
        self.conn.commit()
        result_rows = self.cur.fetchall()
        payment_id = result_rows[0][0]

        user_response = input("Would you like to make this your preferred payment method? (y/n, blank is y)")
        match user_response:
            case 'y' | 'Y' | '':
                self.update_preferred_payment_method(payment_id)

        return PaymentMethodEntry(
            id=payment_id,
            card_number=card_number,
            card_expiration=card_expiration,
            card_code=card_code,
            billing_address_id=billing_address.id,
            customer_id=self._customer_id
        )

    def prompt_user_to_select_payment_method(self) -> PaymentMethodEntry:
        # Checking to see if user has a primary address
        billing_address = None
        self.cur.execute("""
            SELECT a.*
            FROM addresses as a
            INNER JOIN customers as c ON c.primary_address_id = a.id AND c.id = %s
        """,
        (self._customer_id,))
        result_rows = self.cur.fetchall()
        if (len(result_rows) == 1):
            billing_address = AddressEntry(
                id=result_rows[0][0],
                country=result_rows[0][1],
                administrative_division=result_rows[0][2],
                city=result_rows[0][3],
                line1=result_rows[0][4],
                line2=result_rows[0][5],
                postal_code=result_rows[0][6],
                customer_id=result_rows[0][7]
            )
        elif (len(result_rows) == 0):
            print("No address found. Please enter information for a billing address")
            self.prompt_user_to_select_address()
        else:
            print(f"There are {len(result_rows)} result rows??")
            return

        # Getting payment methods
        self.cur.execute("SELECT * FROM payment_methods WHERE customer_id = %s", (self._customer_id,))
        payment_method_rows = self.cur.fetchall()
        selection_table_headings = ['No.', 'Payment Method']
        selection_table_entries = list()
        for index, payment_method_row in enumerate(payment_method_rows):

            # Getting and censoring card number
            card_number_str = payment_method_row[1]
            censored_card_number_str = self._censor_card_number_str(card_number_str)

            # Filling in the selections table entry
            selection_table_entries.append([
                index + 1,
                censored_card_number_str
            ])

        selection_table_entries.append([len(selection_table_entries) + 1, "New Payment Method"])
        print(tabulate(selection_table_entries, headers=selection_table_headings, tablefmt='fancy_grid'))

        # Getting user selection
        user_selection = -1
        while not (0 < user_selection <= len(selection_table_entries)):
            try:
                user_selection = (int)(input("Please select a payment method (by number): "))
                if not (0 < user_selection <= len(selection_table_entries)):
                    print(f"Invalid selection. Selection must be greater than 0 and less than {len(selection_table_entries) + 1}.")
            except ValueError:
                print(f"Invalid selection. Selection must be greater than 0 and less than {len(selection_table_entries) + 1}.")

        new_payment_method_selection_number = len(selection_table_entries)
        payment_method = None
        if (new_payment_method_selection_number == user_selection):
            payment_method = self.display_new_payment_method_input_options_and_add_payment_method(billing_address)
        else:
            payment_method = PaymentMethodEntry(
                id=payment_method_rows[user_selection - 1][0],
                card_number=payment_method_rows[user_selection - 1][1],
                card_expiration=payment_method_rows[user_selection - 1][2],
                card_code=payment_method_rows[user_selection - 1][3],
                billing_address_id=payment_method_rows[user_selection - 1][4],
                customer_id=payment_method_rows[user_selection - 1][5]
            )

        return payment_method


    def get_primary_address(self) -> AddressEntry:
        # Getting the primary address for the customer
        self.cur.execute("""
            SELECT a.*
            FROM addresses as a
            INNER JOIN customers as c ON c.primary_address_id = a.id AND c.id = %s
        """,
        (self._customer_id,))
        result_rows = self.cur.fetchall()
        if (len(result_rows) != 1):
            print("No primary address found")
            return None
        
        address_id, country, administrative_division, city, line1, line2, postal_code, _ = result_rows[0]
        return AddressEntry(
            id=address_id,
            country=country,
            administrative_division=administrative_division,
            city=city,
            line1=line1,
            line2=line2,
            postal_code=postal_code,
            customer_id=self._customer_id
        )

    def create_delivery_for_purchase(self, purchase: PurchaseEntry, address: AddressEntry) -> DeliveryEntry:
        # Defining the query
        self.cur.execute("""
            INSERT INTO deliveries (purchase_id, address_id) VALUES
            (%s, %s)
            RETURNING id, delivery_status
            """,
            (purchase.id, address.id,)
        )
        delivery_id = None
        delivery_status = None
        try:
            delivery_id, delivery_status = self.cur.fetchall()[0]
        except:
            print(f"Error getting delivery id and status for purchase {purchase.id}. Please try again later.\nIf the issue persists, contact customer support.")
            return
        self.conn.commit()

        delivery: DeliveryEntry = DeliveryEntry(
            id=delivery_id,
            purchase_id=purchase.id,
            address_id=address.id,
            delivery_status=delivery_status,
            shipped_on=None,
            estimated_delivery_time=None
        )
        return delivery

    def get_deliveries_by_id(self, delivery_ids: list[int]):
        delivery_query_str: str = """
            SELECT *
            FROM deliveries
            WHERE id = 
        """
        for i in range(len(delivery_ids)):
            delivery_query_str += "%s"
            if (i < len(delivery_ids) - 1):
                delivery_query_str += "OR id = "

        self.cur.execute(delivery_query_str, (delivery_ids))
        delivery_rows = self.cur.fetchall()
        if (len(delivery_rows) == 0):
            return list()
        deliveries = list()
        for row in delivery_rows:
            deliveries.append(DeliveryEntry(
                id=row[0],
                purchase_id=row[1],
                address_id=row[2],
                delivery_status=row[3],
                shipped_on=row[4],
                estimated_delivery_time=row[5]
            ))
        return deliveries


    def empty_cart_and_create_purchase(self, paymentMethod: PaymentMethodEntry) -> PurchaseEntry:
        """
        Empties all items from the cart, adds a purchase to the database,
        adds a product sale for each purchased product to the database.

        Parameters
        -------
        paymentMethod : PaymentMethodEntry
            The payment method being used in the purchase.
        
        Returns
        ------- 
        int
            The ID of the purchase.
        """

        if (len(self._cart) == 0):
            print("Cart is already empty, nothing to purchase.")
            return

        purchase: PurchaseEntry | None = None
        product_sales: list[ProductSalesEntry] = list()
        purchase_id: int | None = None
        created_at: datetime | None = None
        total_cost = Decimal(0.00)

        product_names_query = """
            SELECT id, product_name, price FROM products WHERE removed_at IS NULL AND id IN (
        """
        number_of_unique_items_in_cart = len(self._cart.keys())
        for index, key in enumerate(self._cart.keys()):
            product_names_query += str(key)
            if (index < number_of_unique_items_in_cart - 1):
                product_names_query += ", "
        product_names_query += ")"

        # Executing the query
        self.cur.execute(product_names_query)
        product_rows = self.cur.fetchall()
        if (len(product_rows) != number_of_unique_items_in_cart):
            raise ValueError(f"Expected {number_of_unique_items_in_cart} items, got {len(product_rows)} from database.")

        # Summing up prices, calculating the total cost
        for product_row in product_rows:
            total_cost += (product_row[2] * self._cart[product_row[0]])

        user_response = input(f"Confirm Purchase (total: ${total_cost})? (y/n)")
        match user_response:
            case 'y' | 'Y':
                pass
            case 'n' | 'N':
                print("Purchase canceled.")
                return None
            case _:
                print("Purchase canceled.")
                return None

        # Creating the purchase
        self.cur.execute("""
            INSERT INTO purchases (customer_id, payment_method_id) VALUES
            (%s, %s)
            RETURNING id, created_at;
            """,
            (self._customer_id, paymentMethod.id,)
        )
        self.conn.commit()
        try:
            result = self.cur.fetchall()
            purchase_id = int(result[0][0])
            created_at = result[0][1]
        except ValueError as e:
            print(f"Error creating purchase: {e}")
            return

        purchase = PurchaseEntry(
            id=purchase_id,
            created_at=created_at,
            customer_id=self._customer_id,
            payment_method_id=paymentMethod.id
        )

        # Creating the insertion queries
        sale_insertions_query: str = "INSERT INTO product_sales (purchase_id, product_id, price_per_item, quantity) VALUES "
        sale_insertions_query_values = list()
        for index, product_row in enumerate(product_rows):
            product_id = product_row[0]
            price_per_item = product_row[2]
            quantity = self._cart[product_id]
            # total_cost += (price_per_item * quantity)
            product_sales.append(ProductSalesEntry(
                id=None,
                purchase_id=purchase_id,
                product_id=product_id,
                price_per_item=price_per_item,
                quantity=quantity
            ))
            sale_insertions_query_values.append((purchase_id, product_id, price_per_item, quantity))
            sale_insertions_query += "(%s, %s, %s, %s)"
            if (index < len(product_rows) - 1):
                sale_insertions_query += ", "

        sale_insertions_query += " RETURNING id"

        flattened_sale_insertions_query_values: tuple = tuple(itertools.chain.from_iterable(sale_insertions_query_values))
        self.cur.execute(sale_insertions_query, flattened_sale_insertions_query_values)
        self.conn.commit()
        # sale_ids = [row[0] for row in self.cur.fetchall()]
        insertion_rows = self.cur.fetchall()
        for index, row in enumerate(insertion_rows):
            # product_sales[index].id = row[0]
            product_sales[index] = product_sales[index]._replace(id=row[0])

        # Clearing the cart
        self._cart = dict()

        print("Purchase complete! ✅")

        return purchase

    def display_checkout_options(self) -> bool:
        print("\n===== Checkout =====")
        self.display_current_cart

        shipping_address = self.get_primary_address()
        print("== Shipping Information ==")
        if (shipping_address != None):
            user_response = input(f"Would you like to ship to your primary address {shipping_address.line1}?\n(y/n, blank is y): ")
            match user_response:
                case 'y' | 'Y' | '':
                    pass
                case _:
                    shipping_address = None

        if (shipping_address == None):
            shipping_address = self.prompt_user_to_select_address()

        # Getting the saved billing information
        primary_payment_method_query = sql.SQL("""
            SELECT 
                p.id,
                p.card_number, 
                p.card_expiration, 
                p.card_code, 
                p.billing_address_id,
                a.country, 
                a.administrative_division, 
                a.city, 
                a.line1, 
                a.line2, 
                a.postal_code
            FROM payment_methods AS p
            INNER JOIN customers as c ON c.preferred_payment_id = p.id AND c.id = %s
            INNER JOIN addresses as a ON a.id = p.billing_address_id;
        """)
        self.cur.execute(primary_payment_method_query, (self._customer_id,))

        payment_method = None
        result_rows = self.cur.fetchall()
        if (len(result_rows) < 1):
            # The customer has no primary payment method
            payment_method = self.prompt_user_to_select_payment_method()
        else:
            payment_method_id, card_number, card_expiration, card_code, billing_address_id, country, administrative_division, city, line1, line2, postal_code = result_rows[0]
            card_expiration = None
            # try:
                # card_expiration = datetime.strptime(card_exp_str, "%m/%y")
            # except:
                # print("Something went wrong with fetching preferred payment method card data.")
                # payment_method = self.promptUserToSelectPaymentMethod(conn, cur)

            payment_method = PaymentMethodEntry(
                id=payment_method_id,
                card_number=card_number,
                card_expiration=card_expiration,
                card_code=card_code,
                billing_address_id=billing_address_id,
                customer_id=self._customer_id
            )
            address = AddressEntry(
                id=billing_address_id,
                country=country,
                administrative_division=administrative_division,
                city=city,
                line1=line1,
                line2=line2,
                postal_code=postal_code,
                customer_id=self._customer_id
            )

            user_response = input(f"Would you like to use payment method {self._censor_card_number_str(card_number)}? (y/n, blank is y)")
            match user_response:
                case 'y' | 'Y' | '':
                    pass
                case _:
                    payment_method = self.prompt_user_to_select_payment_method()

        # Nice! Now we have the payment method, and the address to ship to.
        purchase = self.empty_cart_and_create_purchase(payment_method)
        if (purchase != None):
            self.create_delivery_for_purchase(purchase, shipping_address)
        
        return True

    def display_remove_from_cart_options(self, previous_page: Callable):
        try:
            print("\nRemoving items from cart")
            self.display_current_cart()

            product_id = (int)(input("Enter the product ID of the product to remove from your cart: "))
            quantity_str = input("quantity to remove (leave blank for all): ")
            quantity = 0
            query = sql.SQL("SELECT product_name FROM products WHERE removed_at IS NULL AND id = %s")
            self.cur.execute(query, (product_id,))

            # If the product does not exist, notify the user and return to the previous page
            product_rows = self.cur.fetchall()
            if (len(product_rows) < 1):
                print("Invalid product ID, please try again.")
                return previous_page

            if not (product_id in self._cart.keys()):
                print(f"Product ID {product_id} is not in cart, please try again.")
                print(f"current cart: {self._cart.items()}")
                return previous_page

            product_name = product_rows[0]

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

            self.cur.execute(update_query_str, (quantity, product_id,))
            self.conn.commit()

            print(f"Sucessfully removed '{product_name}' from cart.")
            return previous_page
            
        except ValueError:
            print("Invalid input, please try again")
            return previous_page

    def display_add_to_cart_options(self, previous_page: Callable[[cursor.Cursor], None]):
        try:
            product_id = int(input("Enter the product ID of the product to add: "))
            quantity = int(input("quantity: "))
            if (quantity < 1):
                print("Quantity cannot be less than 1")
                return previous_page

            query = sql.SQL("SELECT product_name, stock, price FROM products WHERE removed_at IS NULL AND id = %s")
            self.cur.execute(query, (product_id,))

            # If the product ID is invalid, notify user and return to previous page
            product_rows = self.cur.fetchall()
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
                
            self.cur.execute(update_query_str, (quantity, product_id,))
            self.conn.commit()

            # Updating cart
            if (product_id in self._cart.keys()):
                self._cart[product_id] += quantity
            else:
                self._cart[product_id] = quantity
            return previous_page

        except ValueError:
            print("Invalid input, please try again.")
            return previous_page

    def display_current_cart(self):
        print("Current cart: ")
        table_headings = ["Product ID", "Product Name", "Count", "Price"]

        # Constructing the query
        if (len(self._cart.items()) == 0):
            print("Cart is empty")
            return
        
        product_names_query = """
            SELECT id, product_name, price FROM products WHERE removed_at IS NULL AND id IN (
        """
        number_of_items_in_cart = len(self._cart.keys())
        for index, key in enumerate(self._cart.keys()):
            product_names_query += str(key)
            if (index < number_of_items_in_cart - 1):
                product_names_query += ", "
        product_names_query += ")"

        # Executing the query, printing the table
        self.cur.execute(product_names_query)
        product_rows = self.cur.fetchall()
        table_contents = list()
        total_price = Decimal(0.00)
        for row in product_rows:
            product_id = row[0]
            product_name = row[1]
            price = row[2] * self._cart[product_id]
            total_price += price
            table_contents.append([product_id, product_name, self._cart[product_id], f"${price.quantize(Decimal("0.00"))}"])

        table_contents.append(["Total", "", "", f"${total_price.quantize(Decimal("0.00"))}"])

        print(tabulate(table_contents, headers=table_headings, tablefmt="fancy_grid"))

        # Showing the next options
        return

    def display_purchase_history(self, offset: int = 0) -> bool:
        # Defining the query
        # The query gets every delivery, as well as the associated purchase of each delivery
        # The query should also get the items in each delivery
        # The query should return pages of items 10 at a time
        should_continue: bool = True
        while (should_continue):
            local_purchase_history: dict[int, PurchaseHistoryEntry] = dict()
            purchase_history_query = sql.SQL("""
                SELECT p.*, d.*, s.*, prod.product_name, a.line1
                FROM deliveries as d
                INNER JOIN purchases as p ON d.purchase_id = p.id AND p.customer_id = %s
                INNER JOIN product_sales as s ON p.id = s.purchase_id
                INNER JOIN products as prod ON s.product_id = prod.id
                INNER JOIN addresses as a ON d.address_id = a.id
                ORDER BY d.id
            """)
            self.cur.execute(purchase_history_query, (self._customer_id,))

            # Filling the local purchase history
            result_rows = self.cur.fetchall()

            for result_row in result_rows:
                purchase: PurchaseEntry = PurchaseEntry(
                    id=result_row[0],
                    created_at=result_row[1],
                    customer_id=result_row[2],
                    payment_method_id=result_row[3]
                )
                delivery: DeliveryEntry = DeliveryEntry(
                    id=result_row[4],
                    purchase_id=result_row[5],
                    address_id=result_row[6],
                    delivery_status=result_row[7],
                    shipped_on=result_row[8],
                    estimated_delivery_time=result_row[9]
                )
                sale: ProductSalesEntry = ProductSalesEntry(
                    id=result_row[10],
                    purchase_id=result_row[11],
                    product_id=result_row[12],
                    price_per_item=result_row[13],
                    quantity=result_row[14]
                )
                product_name: str = result_row[15]
                address_line1 = result_row[16]
                if not (purchase.id in local_purchase_history):
                    local_purchase_history[purchase.id] = PurchaseHistoryEntry(
                        purchase=purchase,
                        deliveries={delivery.id: (delivery, address_line1)},
                        sales={sale.id: (sale, product_name)}
                    )
                else:
                    local_purchase_history[purchase.id].deliveries[delivery.id] = (delivery, address_line1)
                    local_purchase_history[purchase.id].sales[sale.id] = (sale, product_name)

            # Pretty printing the table
            purchase_history_headers = ["Purchase\nID", "Items in Purchase", "Delivery Status", "Total\nPrice"]
            purchase_history_table_entries = list()
            for id, purchase in local_purchase_history.items():
                sales_str = ""
                deliveries_str = ""

                # Creating the sales str
                total_price: Decimal = Decimal("0.00")
                sales_table_entries = list()
                sales_str = "== Items Purchased ==\n"
                for sale_id, sale_info in purchase.sales.items():
                    sale = sale_info[0]
                    product_name = sale_info[1]
                    # sales_str += f"- {strict_truncate_str(product_name, 20)}: {sale.quantity} (${(sale.price_per_item * sale.quantity).quantize(Decimal("0.00"))})\n"
                    sales_table_entries.append([
                        f"- {textwrap.fill(product_name, 20, subsequent_indent="  ")}",
                        f"({sale.quantity})",
                        f"${(sale.price_per_item * sale.quantity).quantize(Decimal("0.00"))}"
                    ])
                    # sales_str += f"- {textwrap.fill(product_name, 20, subsequent_indent="    ")}: {sale.quantity} (${(sale.price_per_item * sale.quantity).quantize(Decimal("0.00"))})\n"
                    total_price += sale.price_per_item * sale.quantity
                sales_str = tabulate(sales_table_entries, tablefmt='plain')

                # Creating the deliveries str
                deliveries_str = "== Deliveries ==\n"
                for delivery_id, delivery_info in purchase.deliveries.items():
                    delivery = delivery_info[0]
                    address_line1 = delivery_info[1]
                    deliveries_str += f"""
- Delivery ID: {delivery_id}
    - Shipped to: {textwrap.fill(address_line1, 25)}
    - Status: {delivery.delivery_status}
                    """
                    if (delivery.shipped_on != None):
                        deliveries_str += f"    - Shipped on {delivery.shipped_on.isoformat()}"
                    if (delivery.estimated_delivery_time != None):
                        deliveries_str += f"    - Estimated delivery time: {delivery.estimated_delivery_time.isoformat()}"

                purchase_history_table_entries.append([
                    id,
                    sales_str,
                    deliveries_str,
                    f"${total_price}"
                ])

            print(tabulate(purchase_history_table_entries, headers=purchase_history_headers, tablefmt='fancy_grid'))

            should_continue = False
        
        return True

    def get_customer_report_and_report_product(self, product_id: int | None = None, report_reason: ReportReason | None = None) -> ReportEntry | None:
        # Getting the product id
        while (product_id == None):
            product_id_str = input("Please enter the product ID: ")
            try:
                product_id = int(product_id_str)
            except ValueError:
                print("Invalid product id. Please try again.")
                product_id = None

        # Getting the report reason
        if (report_reason == None):
            # Printing out the table
            report_options_headers = ["No.", "Reason"]
            report_options_entries = [
                (1, ReportReason.FALSE_ADVERTISING),
                (2, ReportReason.INNAPROPRIATE_CONTENT),
                (3, ReportReason.ILLEGAL_PRODUCT),
                (4, ReportReason.CUSTOM)
            ]
            num_of_report_options: int = len(report_options_entries)
            selected_report_option_num: int | None = None
            print(tabulate(report_options_entries, headers=report_options_headers, tablefmt='rounded_grid'))
            while (report_reason == None):
                user_response = input("Please select a report option (by number). ")
                try:
                    selected_report_option_num = int(user_response)
                    if not (0 < selected_report_option_num <= num_of_report_options):
                        print(f"Please select a valid report option, 1 - {num_of_report_options}")
                        continue
                except ValueError:
                    print(f"Please select a valid report option, 1 - {num_of_report_options}")
                    continue
                report_reason = report_options_entries[selected_report_option_num - 1][1]
                if (report_reason == ReportReason.CUSTOM):
                    # Getting custom report reason.
                    while (True):
                        user_response = input("Please enter in the report reason.")
                        if (len(user_response) > 60):
                            print("Reason too long. Please try again (max 60 characters).")
                        else:
                            report_reason = user_response
                            break

        # Saving report in database
        self.cur.execute(
            sql.SQL("""
                INSERT INTO reports (customer_id, product_id, reason) VALUES
                (%s, %s, %s)
                RETURNING id, reviewed_by, created_at
            """),
            (self._customer_id, product_id, report_reason,)
        )
        self.conn.commit()
        result_rows = self.cur.fetchall()
        if (len(result_rows) == 0):
            print("Something went wrong.")
            return None

        print("Your report has been submitted and will be reviewed.")

        return ReportEntry(
            id=result_rows[0][0],
            customer_id=self._customer_id,
            reviewed_by=result_rows[0][1],
            reason=report_reason,
            created_at=result_rows[0][2]
        )

    def get_customer_rating_and_rate_product(self, product_id: int | None = None, rating: int | None = None) -> RatingEntry:
        """
        Gets rating from user input and adds rating of a given product
        to the database.

        Parameters
        -------
            product_id: int
                The ID of the product being rated
                
        Returns
        ------- 
            RatingEntry
                The newly created rating
        """

        # If the product_id is not given, get it from user input
        while (product_id == None):
            product_id_str = input("Please enter the product ID: ")
            try:
                product_id = int(product_id_str)
            except ValueError:
                print("Invalid product id. Please try again.")
                product_id = None

        # Verify the database has a product with the given id
        # self.cur.execute(sql.SQL("SELECT name FROM products INNER JOIN  id = %s"), (product_id,))
        product_selection_query = sql.SQL("""
            SELECT DISTINCT p.product_name
            FROM products as p
            INNER JOIN product_sales as s 
                ON s.product_id = p.id AND p.id = %s
            INNER JOIN purchases 
                ON s.purchase_id = purchases.id AND purchases.customer_id = %s
        """)
        self.cur.execute(product_selection_query, (product_id, self._customer_id,))
        result_rows = self.cur.fetchall()
        if (len(result_rows) != 1):
            print("You can only rate products that you have purchased.")
            return None

        # Getting rating if not given
        number_of_rating_attempts = 0
        while (rating == None):
            rating_str = input("Please enter a rating for the product (1 through 10): ")
            if (number_of_rating_attempts > 4 and rating_str == 'x'):
                return None
            number_of_rating_attempts += 1
            try:
                if (number_of_rating_attempts > 4):
                    print("Press x to exit the rating menu.")
                rating = int(rating_str)
                if not (0 < rating <= 10):
                    print("Invalid rating.", end=" ")
            except ValueError:
                print("Invalid rating.", end=" ")

        # Add a rating to the database
        self.cur.execute(sql.SQL("""
            INSERT INTO ratings (customer_id, product_id, rating) VALUES
            (%(customer_id)s, %(product_id)s, %(rating)s)
            ON CONFLICT (customer_id, product_id)
            DO UPDATE SET rating = %(rating)s
            RETURNING created_at
            """),
            {
                "customer_id": self._customer_id, 
                "product_id": product_id, 
                "rating": rating
            }
        )
        self.conn.commit()
        print(f"Successfully rated {result_rows[0][0]} {rating}")
        return RatingEntry(
            customer_id=self._customer_id,
            product_id=product_id,
            rating=rating,
            created_at=self.cur.fetchall()[0][0]
        )

    def list_products(self):
        # Getting the products
        query = """
            SELECT p.id, p.product_name, p.stock, s.seller_name, r.average_rating, p.price
            FROM products as p
            JOIN sellers as s ON p.seller_id = s.id
            FULL OUTER JOIN (
                SELECT r.product_id, AVG(r.rating) as average_rating
                FROM ratings as r
                GROUP BY r.product_id
            ) as r ON r.product_id = p.id
            WHERE p.removed_at IS NULL
            ;
        """
        self.cur.execute(query)
        product_rows = self.cur.fetchall()
        for index, product_row in enumerate(product_rows):
            product_rows[index] = (
                product_row[0],
                product_row[1],
                product_row[2],
                product_row[3],
                product_row[4],
                f"${product_row[5].quantize(Decimal("0.00"))}",
            )
        print("\nProducts:")
        print(tabulate(product_rows, headers = ["ID", "Name", "Stock", "Seller", "Rating", "Price"], tablefmt="fancy_grid"))

        # Presenting customer options   
        user_options = [
            ["Add to Cart", "Remove from Cart", "Rate", "Report", "View Cart", "Checkout"],
            ["a", "s", "d", "f", "v", "c"]
        ]
        print("Controls: ")
        print(tabulate([user_options[1]], user_options[0], tablefmt = "simple"))

        # Getting the user input
        user_input = input()
        match user_input:
            case 'a' | 'A':
                # Add to cart
                next_page = self.display_add_to_cart_options(self.list_products)
                next_page()
            case 's' | 'S':
                # Remove from Cart
                next_page = self.display_remove_from_cart_options(self.list_products)
                next_page()
            case 'd' | 'D':
                # Rate
                self.get_customer_rating_and_rate_product()
                return True
            case 'f' | 'F':
                # Report
                self.get_customer_report_and_report_product()
                return True
            case 'v' | 'V':
                # View cart
                self.display_current_cart()
                return True
            case 'c' | 'C':
                # Checkout
                self.display_checkout_options()
                return True
            
        return True

    def _censor_card_number_str(self, card_number_str: str) -> str:
        censored_card_number_str = ""
        card_number_len = len(card_number_str)
        for i in range(card_number_len):
            if (i == 0):
                censored_card_number_str += card_number_str[i]
            elif (i > card_number_len - 5):
                censored_card_number_str += card_number_str[i]
            elif (i % 4 == 0):
                censored_card_number_str += "* "
            else:
                censored_card_number_str += "*"
        return censored_card_number_str