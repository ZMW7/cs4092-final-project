import psycopg
from commonTypes import AddressEntry, PaymentMethodEntry, PurchaseEntry, ProductSalesEntry, DeliveryEntry, RatingEntry, ReportEntry, PurchaseHistoryEntry, ProductEntry
from decimal import Decimal
from psycopg import sql
from datetime import datetime, date
from tabulate import tabulate
import plotext

class SellerView:

    def __init__(self, conn: psycopg.connection.Connection, cur: psycopg.cursor.Cursor, username: str):
        self.connection: psycopg.connection.Connection = conn
        self.cursor: psycopg.cursor.Cursor = cur

        print(f'Seller name is {username}')
        # Getting seller ID
        self.cursor.execute(
            sql.SQL("""
                SELECT s.id FROM sellers AS s WHERE s.seller_name = %s
            """),
            (username,)
        )
        result_rows = self.cursor.fetchall()
        if (len(result_rows) > 1):
            print(f"Something went wrong. More than one merchant has been found with the name '{username}'.")
            return
        elif (len(result_rows) < 1):
            print(f"Something went wrong. No merchants found with the name '{username}'.")
            return
        self._seller_id = result_rows[0][0]
        self._seller_name = username

    def display_current_products(self):
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                SELECT id, product_name, stock, price, created_at FROM products AS p WHERE p.seller_id = %s
            """),
            (self._seller_id,)
        )
        result_rows = self.cursor.fetchall()
        products: list[ProductEntry] = list()
        for row in result_rows:
            products.append(ProductEntry(
                id=row[0],
                product_name=row[1],
                stock=row[2],
                seller_id=self._seller_id,
                price=row[3],
                created_at=row[4]
            ))

        # Creating output table
        output_table_headers = ["ID", "Name", "Stock", "Price", "Creation time"]
        output_table_entries = list()
        for product in products:
            output_table_entries.append([product.id, product.product_name, product.stock, product.price, product.created_at])

        print(tabulate(output_table_entries, headers=output_table_headers, tablefmt='rounded_grid'))


    def display_sales_chart(self, product_id: int, start_datetime: datetime | None, end_datetime: datetime | None):
        if (end_datetime == None):
            end_datetime = datetime.now()
        if (start_datetime == None):
            # Defining and executing the query 
            self.cursor.execute(
                sql.SQL("""
                    SELECT s.quantity, p.created_at
                    FROM purchases AS p
                    INNER JOIN product_sales as s
                        ON s.purchase_id = p.id AND p.created_at < %(end_datetime)s
                    INNER JOIN products as prod
                        ON prod.id = s.product_id AND prod.id = %(product_id)s AND prod.seller_id = %(seller_id)s
                    ORDER BY p.created_at
                """),
                {"product_id": product_id, "end_datetime": end_datetime, "seller_id": self._seller_id}
            )
        else:
            # Defining and executing the query
            self.cursor.execute(
                sql.SQL("""
                    SELECT s.quantity, p.created_at
                    FROM purchases as p
                    INNER JOIN product_sales as s
                        ON s.purchase_id = p.id AND p.created_at >= %(start_datetime)s AND p.created_at < %(end_datetime)s
                    INNER JOIN products as prod
                        ON prod.id = s.product_id AND prod.id = %(product_id)s AND prod.seller_id = %(seller_id)s
                    ORDER BY p.created_at
                """),
                {"product_id": product_id, "start_datetime": start_datetime, "end_datetime": end_datetime, "seller_id": self._seller_id}
            )
        result_rows = self.cursor.fetchall()

        # Plotting data
        sales: list[int] = list()
        times: list[datetime] = list()
        previous_sum = 0
        for index, row in enumerate(result_rows):
            sales.append(row[0] + previous_sum)
            times.append(row[1])
            previous_sum += row[0]

        time_strings = plotext.datetimes_to_strings(times, output_form='Y-m-d H:M:S')

        plotext.date_form(input_form='Y-m-d H:M:S', output_form='Y-m-d H:M:S')
        plotext.plot(time_strings, sales)
        plotext.title(f"Sales of {product_id}")
        plotext.xlabel("Date and Time")
        plotext.ylabel("Sales")
        plotext.show()
        plotext.clear_data()

    def display_earnings_chart(self, start_datetime: datetime | None, end_datetime: datetime | None):
        if (end_datetime == None):
            end_datetime = datetime.now()
        if (start_datetime == None):
            # Defining and executing the query 
            self.cursor.execute(
                sql.SQL("""
                    SELECT s.quantity * s.price_per_item AS total_price, p.created_at
                    FROM purchases AS p
                    INNER JOIN product_sales as s
                        ON s.purchase_id = p.id AND p.created_at < %(end_datetime)s
                    INNER JOIN products as prod
                        ON prod.id = s.product_id AND prod.seller_id = %(seller_id)s
                    ORDER BY p.created_at
                """),
                {"end_datetime": end_datetime, "seller_id": self._seller_id}
            )
        else:
            # Defining and executing the query
            self.cursor.execute(
                sql.SQL("""
                    SELECT s.quantity * s.price_per_item AS total_price, p.created_at
                    FROM purchases as p
                    INNER JOIN product_sales as s
                        ON s.purchase_id = p.id AND p.created_at >= %(start_datetime)s AND p.created_at < %(end_datetime)s
                    INNER JOIN products as prod
                        ON prod.id = s.product_id AND prod.seller_id = %(seller_id)s
                    ORDER BY p.created_at
                """),
                {"start_datetime": start_datetime, "end_datetime": end_datetime, "seller_id": self._seller_id}
            )
        result_rows = self.cursor.fetchall()

        # Plotting data
        earnings: list[int] = list()
        times: list[datetime] = list()
        previous_sum = 0
        for index, row in enumerate(result_rows):
            earnings.append(float(row[0]) + previous_sum)
            times.append(row[1])
            previous_sum += float(row[0])

        time_strings = plotext.datetimes_to_strings(times, output_form='Y-m-d H:M:S')

        plotext.date_form(input_form='Y-m-d H:M:S', output_form='Y-m-d H:M:S')
        plotext.plot(time_strings, earnings)
        plotext.title(f"Earnings (USD)")
        plotext.xlabel("Date and Time")
        plotext.ylabel("Sales")
        plotext.show()
        plotext.clear_data()
        

    def add_product_to_market(self, product_name: str, stock: int, price: Decimal) -> ProductEntry | None:
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                INSERT INTO products (product_name, stock, seller_id, price) VALUES
                (%s, %s, %s, %s)
                RETURNING id, created_at
            """),
            (product_name, stock, self._seller_id, price,)
        )
        self.connection.commit()
        result_rows = self.cursor.fetchall()
        if (len(result_rows) != 1):
            print("Error in adding product to market.")
            return
        added_product = ProductEntry(
            id=result_rows[0][0],
            product_name=product_name,
            stock=stock,
            seller_id=self._seller_id,
            price=price,
            created_at=result_rows[0][1]
        )
        return added_product

    def adjust_product_price(self, product_id: int, price: Decimal) -> ProductEntry | None:
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                UPDATE products
                SET price = %(price)s
                WHERE id = %(product_id)s AND seller_id = %(seller_id)s
                RETURNING id, product_name, stock, seller_id, price, created_at
            """),
            {"price": price, "product_id": product_id, "seller_id": self._seller_id}
        )
        self.connection.commit()
        result_rows = self.cursor.fetchall()
        if (len(result_rows) < 1):
            print(f"No product sold by {self._seller_name} with id {product_id} found.")
            return None
        elif (len(result_rows) > 1):
            print("Something went wrong. Please try again.")
            return None
        
        return ProductEntry(
            id=result_rows[0][0],
            product_name=result_rows[0][1],
            stock=result_rows[0][2],
            seller_id=result_rows[0][3],
            price=result_rows[0][4],
            created_at=result_rows[0][5]
        )

    def add_to_product_stock(self, product_id: int, stock_change: int):
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                UPDATE products
                SET stock = stock + %(stock_change)s
                WHERE id = %(product_id)s AND seller_id = %(seller_id)s
                RETURNING id, product_name, stock, seller_id, price, created_at
            """),
            {"stock_change": stock_change, "product_id": product_id, "seller_id": self._seller_id}
        )
        self.connection.commit()
        result_rows = self.cursor.fetchall()
        if (len(result_rows) < 1):
            print(f"No product sold by {self._seller_name} with id {product_id} found.")
            return None
        elif (len(result_rows) > 1):
            print("Something went wrong. Please try again.")
            return None
        
        return ProductEntry(
            id=result_rows[0][0],
            product_name=result_rows[0][1],
            stock=result_rows[0][2],
            seller_id=result_rows[0][3],
            price=result_rows[0][4],
            created_at=result_rows[0][5]
        )

    def get_user_input_for_adding_product(self) -> tuple[str, int, Decimal]:
        user_response: str | None = None
        print("=== Create a new product ===")

        user_response = input("Product name: ")
        while not (self._product_name_is_valid(user_response)):
            print("Invalid product name. Please try again.", end=" ")
            user_response = input("Product name: ")
        product_name = user_response

        user_response = input("Stock: ")
        while not (self._product_stock_string_is_valid(user_response) and int(user_response) >= 0):
            print("Invalid stock amount. Please try again.", end=" ")
            user_response = input("Stock: ")
        product_stock = int(user_response)

        user_response = input("Price: $")
        while not (self._product_price_string_is_valid(user_response)):
            print("Invalid price. Please try again.")
            user_response = input("Price: $")
        product_price = self._convert_price_string_to_price(user_response)

        return (product_name, product_stock, product_price)

    def get_user_input_for_product_id(self) -> int:
        product_id: int | None = None
        user_response: str = ""
        # Getting product id
        while (product_id == None):
            user_response = input("Product ID: ")
            try:
                product_id = int(user_response)
            except ValueError:
                print("Invalid product id. Please try again.", end=" ")
        return product_id

    def get_user_input_for_datetime(self, can_be_none: bool) -> datetime | None:
        result_datetime: datetime | None = None
        while (result_datetime == None):
            result_date: date | None = None
            datetime_string: str = ""
            while (result_date == None):
                date_string: str = ""
                user_prompt = "Please enter the date according to ISO 8601 (YYYY-MM-DD)"
                if (can_be_none):
                    user_prompt += " (can be blank)"
                user_prompt += ": "
                date_string += input(user_prompt)
                if not (can_be_none) or (can_be_none and len(date_string) > 0):
                    try:
                        result_date = date.fromisoformat(date_string)
                    except:
                        print("Invalid date. Please try again.")
                elif (can_be_none and len(date_string) == 0):
                    result_date = None
                    break

            user_prompt = "Please enter the time according to ISO 8601 (HH:MM:SS)"
            if (can_be_none):
                user_prompt += "(can be blank)"
            user_prompt += ".\nAdd a 'Z' to the end for UTC time. Otherwise, system time zone is used. "
            user_prompt += "\nTime: "
            print(user_prompt, end='')
            user_response = input()
            if not (can_be_none) or (can_be_none and len(user_response) > 0):
                temp_date: date = result_date
                if (temp_date == None):
                    temp_date = datetime.now().date()
                try:
                    result_datetime = temp_date.isoformat() + "T" + user_response
                except:
                    print("Invalid time. Please try again.")
            elif (can_be_none and len(user_response) == 0):
                result_datetime = None
                break

        return result_datetime
    

    def get_user_input_for_adjusting_price(self) -> tuple[int, Decimal]:
        user_response: str | None = None
        product_id: int | None = None
        product_price: Decimal | None = None
        print("=== Changing Product Price ===")

        # Getting product id
        product_id = self.get_user_input_for_product_id()

        # Getting product price
        user_response = input("New Price: $")
        while not (self._product_price_string_is_valid(user_response)):
            user_response = input("Invalid price. Please try again.\nNew Price: $")
        product_price = self._convert_price_string_to_price(user_response)
        return (product_id, product_price)

    def get_user_input_for_adjusting_stock(self) -> tuple[int, int]:
        user_response: str | None = None
        product_id: int | None = None
        stock_change: int | None = None
        print("=== Adjusting Stock ===")

        # Getting product id
        product_id = self.get_user_input_for_product_id()

        # Getting the stock adjustment
        user_response = input("Please enter the amount by which the stock is to increase (negative numbers decrease stock): ")
        while not (self._product_stock_string_is_valid(user_response)):
            user_response = input("Invalid stock change. Please try agian.\nStock adjustment: ")
        stock_change = int(user_response)

        return (product_id, stock_change)

    def get_start_and_end_datetimes_input(self) -> tuple[datetime | None, datetime | None]:
        # Getting the start datetime
        print("\n= Start Datetime =")
        start_datetime = self.get_user_input_for_datetime(True)
        print("\n= End Datetime =")
        end_datetime = self.get_user_input_for_datetime(True)
        if (end_datetime == None):
            end_datetime = datetime.now()
        return (start_datetime, end_datetime)

    def get_user_input_for_sales_chart(self) -> tuple[int, datetime | None, datetime | None]:
        print("== Sales Chart ==")
        product_id = self.get_user_input_for_product_id()
        start_datetime, end_datetime = self.get_start_and_end_datetimes_input()
        return (product_id, start_datetime, end_datetime)


    def display_data_menu_and_get_user_input(self):
        print("==== Data Menu ===")
        controls_table_headers: list[str] = ["View Sales Chart", "View Earnings Chart", "Back"]
        controls_table_entries: list[list[str]] = [['s', 'e', 'x']]
        print(tabulate(controls_table_entries, headers=controls_table_headers, tablefmt='simple'))
        user_response = ""
        while (user_response == ""):
            user_response = input()
            match user_response:
                case 's' | 'S':
                    # View sales chart
                    product_id, start_datetime, end_datetime = self.get_user_input_for_sales_chart()
                    self.display_sales_chart(product_id, start_datetime, end_datetime)
                case 'e' | 'E':
                    # View earnings chart
                    print("== Earnings Chart ==")
                    start_datetime, end_datetime = self.get_start_and_end_datetimes_input()
                    self.display_earnings_chart(start_datetime, end_datetime)
                case 'x' | 'X':
                    # Back
                    return
                case _:
                    user_response = ""
                    


    def get_main_menu_user_input(self):
        print(f"Merchant View ---------- {self._seller_name}")
        should_continue: bool = True
        while (should_continue):
            controls_table_headers: list[str] = ["View Products", "Add Product", "Adjust Prices", "Adjust Stock", "See Data", "Sign Out"]
            controls_table_entries: list[list[str]] = [['v', 'a', 't', 's', 'd', 'x']]
            print(tabulate(controls_table_entries, headers=controls_table_headers, tablefmt='simple'))
            user_response = ""
            while (user_response == ""):
                user_response = input()
                match user_response:
                    case 'v' | 'V':
                        # View products
                        self.display_current_products()
                    case 'a' | 'A':
                        # Add product
                        product_name, stock, price = self.get_user_input_for_adding_product()
                        self.add_product_to_market(product_name=product_name, stock=stock, price=price)
                    case 't' | 'T':
                        # Adjust prices
                        product_id, price = self.get_user_input_for_adjusting_price()
                        self.adjust_product_price(product_id, price)
                    case 's' | 'S':
                        # Adjust stock
                        product_id, stock_change = self.get_user_input_for_adjusting_stock()
                        self.add_to_product_stock(product_id=product_id, stock_change=stock_change)
                    case 'd':
                        self.display_data_menu_and_get_user_input()
                    case 'x':
                        should_continue = False
                    case _:
                        user_response = ""

    def beginInteraction(self):
        self.get_main_menu_user_input()


    def _product_name_is_valid(self, product_name: str) -> bool:
        return isinstance(product_name, str) and len(product_name) < 50 and len(product_name) > 1

    def _product_stock_string_is_valid(self, stock_str: str) -> bool:
        if (stock_str == None or len(stock_str) < 1):
            return False
        try:
            stock = int(stock_str)
            return self._product_stock_is_valid(stock)
        except:
            return False

    def _product_stock_is_valid(self, stock: int) -> bool:
        max_int = 2147483647
        min_int = -2147483648
        return (min_int <= stock <= max_int)

    def _convert_price_string_to_price(self, price_str: str) -> Decimal | None:
        clean_str = price_str.replace(",", "")
        # The string should have at least two decimal places
        decimal_places = 0
        if '.' in clean_str:
            decimal_places = len(clean_str.split('.')[1])
        if (decimal_places > 2):
            return None

        decimal_price = Decimal(clean_str)
        return decimal_price

    def _product_price_string_is_valid(self, price_str: str) -> bool:
        if (price_str == None or len(price_str) < 1):
            return False
        try:
            decimal_price = self._convert_price_string_to_price(price_str)
            if (decimal_price == None):
                return False
            return self._product_price_is_valid(decimal_price)
        except:
            return False

    def _product_price_is_valid(self, price: Decimal) -> bool:
        return 0 <= price < 10e8
