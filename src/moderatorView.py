from commonTypes import *
import psycopg
from psycopg import sql
from tabulate import tabulate
import textwrap
from collections.abc import Callable

class ModeratorView:
    """
    This class acts as an interface between moderators and the database.

    Moderators can:
    - Review Reports
    - Remove products from the platform
    - Remove merchants from the platform

    After a moderator reviews a report, they can:
    - Choose to take immediate action, removing the product
    - Choose to view another report made against the same product
    """

    def __init__(self, conn: psycopg.Connection, cur: psycopg.Cursor, moderator_email: str):
        self.connection: psycopg.connection.Connection = conn
        self.cursor: psycopg.cursor.Cursor = cur

        # Getting moderator info
        self.cursor.execute(
            sql.SQL("""
                SELECT id, m.created_at, m.first_name, m.last_name
                FROM moderators as m
                WHERE m.email_address = %s
            """),
            (moderator_email,)
        )
        result_rows = self.cursor.fetchall()
        self._moderator_info = ModeratorInfo(
            id=result_rows[0][0],
            created_at=result_rows[0][1],
            first_name=result_rows[0][2],
            last_name=result_rows[0][3],
            email_address=moderator_email
        )

    def remove_merchant(self, merchant_id: int) -> bool:
        """
        Removes a merchant from the platform.

        Parameters
        -------
            merchant_id: int
                The ID of the merchant being removed
            
        Returns
        -------
            bool
                Whether or not a merchant with the given id was successfully removed
        """
        # Deleting the merchant
        try:
            self.cursor.execute(
                sql.SQL("""
                    UPDATE sellers
                    SET removed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """),
                (merchant_id,)
            )
        except Exception as e:
            print(e)
            return False
        # Deleting all products
        self.cursor.execute(
            sql.SQL("""
                UPDATE products
                SET removed_at = CURRENT_TIMESTAMP
                WHERE seller_id = %s
                RETURNING id
            """),
            (merchant_id,)
        )
        deleted_products = self.cursor.fetchall()

        # Inserting into 'seller_removals' table
        self.cursor.execute(
            sql.SQL("""
                INSERT INTO seller_removals (removed_by, seller_id) VALUES
                (%s, %s)
            """),
            (self._moderator_info.id, merchant_id,)
        )

        #  Inserting into 'product_removals' table
        product_removals_insertions: list[tuple[int, int]] = [ (self._moderator_info.id, merchant_id, deleted_product[0]) for deleted_product in deleted_products ]
        self.cursor.executemany(
            sql.SQL("""
                INSERT INTO product_removals (removed_by, seller_id, product_id) VALUES
                (%s, %s, %s)
            """),
            product_removals_insertions
        )
        self.connection.commit()
        return True

    def remove_product(self, product_id: int) -> bool:
        """
        Removes a product from the platform.

        Parameters
        -------
            product_id: int
                The ID of the product being removed
            
        Returns
        -------
            bool
                Whether or not a product with the given id was successfully removed
        """
        try:
            self.cursor.execute(
                sql.SQL("""
                    UPDATE products
                    SET removed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, seller_id
                """),
                (product_id,)
            )
        except Exception as e:
            print(e)
            return False
        result_rows = self.cursor.fetchall()
        if (len(result_rows) < 1):
            print(f"Product with ID {product_id} does not exist.")
        removed_product_id, seller_id = result_rows[0]
        self.cursor.execute(
            sql.SQL("""
                INSERT INTO product_removals (removed_by, seller_id, product_id) VALUES
                (%s, %s, %s)
            """),
            (self._moderator_info.id, seller_id, removed_product_id)
        )
        self.connection.commit()
        return True

    def mark_report_as_reviewed(self, report_id: int) -> bool:
        try:
            self.cursor.execute(
                sql.SQL("""
                    UPDATE reports
                    SET reviewed_by = %(moderator_id)s
                    WHERE id = %(report_id)s
                    RETURNING id
                """),
                {"moderator_id": self._moderator_info.id, "report_id": report_id}
            )
            return (len(self.cursor.fetchall() == 1))
        except Exception as e:
            return False

    def get_number_of_product_removals_for_merchant(self, seller_id: int) -> int:
        self.cursor.execute(
            sql.SQL("""
                SELECT COUNT(*)
                FROM product_removals
                WHERE seller_id = %s
            """),
            (seller_id,)
        )
        return self.cursor.fetchall()[0][0]

    def display_previously_reviewed_reports(self):
        pass

    def display_unreviewed_reports_for_unreviewed_products(self):
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                SELECT r.id, r.customer_id, r.product_id, r.created_at, r.reason
                FROM reports AS r
                INNER JOIN products AS p ON p.id = r.product_id
                WHERE r.reviewed_by IS NULL AND p.removed_at IS NULL
                ORDER BY r.created_at
            """)
        )
        result_rows = self.cursor.fetchall()

        unreviewed_reports_table_headers: list[str] = ["ID", "Customer ID", "Product ID", "Timestamp", "Reason"]
        unreviewed_reports_table_entries: list[list[str]] = [ [row[0], row[1], row[2], row[3].strftime("%Y-%m-%d %H:%M:%S"), textwrap.fill(row[4], width=20)] for row in result_rows ]
        print("\n== Unreviewed Reports ==")
        print(tabulate(unreviewed_reports_table_entries, headers=unreviewed_reports_table_headers, tablefmt='fancy_grid'))

    def display_product_removal_history(self):
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                SELECT product_id, seller_id, removed_at
                FROM product_removals
                WHERE removed_by = %s
            """),
            (self._moderator_info.id,)
        )
        result_rows = self.cursor.fetchall()
        removal_history_table_headers: list[str] = ["Product ID", "Merchant ID", "Removal Date"]
        print(tabulate(result_rows, headers=removal_history_table_headers, tablefmt='fancy_grid'))

    def display_merchant_removal_history(self):
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                SELECT seller_id, removed_at
                FROM seller_removals
                WHERE removed_by = %s
            """),
            (self._moderator_info.id,)
        )
        result_rows = self.cursor.fetchall()
        removal_history_table_headers: list[str] = ["Merchant ID", "Removal Date"]
        print(tabulate(result_rows, headers=removal_history_table_headers, tablefmt='fancy_grid'))

    def get_product_removal_input(self) -> int:
        """
        Prompts the user to enter the product ID of a product to remove.

        Returns
        ------
            int
                The ID of the product to be removed
        """
        print("\n== Product Removal ==")
        user_response: str = ""
        product_id: int | None = None
        while (user_response == ""):
            user_response = input("Product ID: ")
            try:
                product_id = int(user_response)
            except ValueError:
                user_response = ""
                print("Invalid product ID. Please try again.")
        return product_id

    def get_merchant_removal_input(self) -> int:
        """
        Prompts the user to enter the ID of a merchant to remove.

        Returns
        ------
            int
                The ID of the merchant to be removed
        """
        print("\n== Merchant Removal ==")
        user_response: str = ""
        merchant_id: int | None = None
        while (user_response == ""):
            user_response = input("Merchant ID: ")
            try:
                merchant_id = int(user_response)
            except ValueError:
                user_response = ""
                print("Invalid merchant ID. Please try again.")
        return merchant_id

    def get_info_for_report_review_screen(self, report_id: int) -> tuple[int, str, str, str] | None:
        # Defining and executing the query
        self.cursor.execute(
            sql.SQL("""
                SELECT prod.id, prod.product_name, s.seller_name, s.id, rep.reason
                FROM reports as rep
                INNER JOIN products as prod
                    ON prod.id = rep.product_id
                INNER JOIN sellers as s
                    ON s.id = prod.seller_id
                WHERE prod.removed_at IS NULL AND s.removed_at IS NULL AND rep.id = %s
            """),
            (report_id,)
        )
        result_rows = self.cursor.fetchall()
        if (len(result_rows) != 1):
            return None
        return (result_rows[0][0], result_rows[0][1], result_rows[0][2], result_rows[0][3], result_rows[0][4])
    
    def display_report_review_screen_and_get_product_id(self, report_id: int) -> int:
        product_id: int
        product_name: str
        seller_name: str
        report_reason: str
        product_id, product_name, seller_name, seller_id, report_reason = self.get_info_for_report_review_screen(report_id=report_id)
        print(tabulate([[product_id, product_name, textwrap.fill(seller_name, width=len('Merchant Name')), seller_id, textwrap.fill(report_reason, width=20)]], headers=['Product ID', 'Product Name', 'Merchant Name', 'Merchant\nID', 'Report Reason'], tablefmt='fancy_grid'))
        return product_id

    def handle_report_review_screen(self):
        user_response: str = ""
        report_id: int | None = None
        while (user_response == ""):
            user_response = input("Enter the ID of a report to review, or 'x' to return to the main menu: ")
            match user_response:
                case 'x':
                    return
                case _:
                    pass
            try:
                report_id = int(user_response)
                if (report_id < 1):
                    user_response = ""
                    print("Invalid response.")
            except ValueError:
                user_response = ""
                print("Invalid response.")
                continue
        
        # Displaying report review screen and controls
        product_id = self.display_report_review_screen_and_get_product_id(report_id=report_id)
        controls_table_headers: list[str] = ['Remove Product', 'Ignore']
        controls_table_entries: list[list[str]] = [['o', 'i']]
        print(tabulate(controls_table_entries, headers=controls_table_headers, tablefmt='simple'))

        # Getting user input
        user_response = ""
        while (user_response == ""):
            user_response = input()
            match user_response:
                case 'o' | 'O':
                    # Remove Product
                    self.remove_product(product_id=product_id)
                case 'i' | 'I':
                    # Ignore report
                    pass
                case _:
                    print("Invalid response")
                    user_response = ""
        self.mark_report_as_reviewed(report_id=report_id)


    def get_user_choice_in_response_to_display_of_unreviewed_reports(self) -> Callable | None:
        """
        Prompts the user to select an action to take in response to a previously displayed table of unreviewed reports

        Returns
        -------
            Callable
                The function to be called next according to the user's input
            None
                An invalid item is inputted
        """
        controls_table_headers: list[str] = ["Review Report"]
        controls_table_entries: list[list[str]] = [['e']]
        print(tabulate(controls_table_entries, headers=controls_table_headers, tablefmt='simple'))
        user_response: str = input()
        match user_response:
            case 'e' | 'E':
                return self.handle_report_review_screen
            case _:
                print("Invalid choice")
                return None

    def get_history_function_based_on_input(self) -> Callable | None:
        """
        Prompts the user to select a form of history to view (removed products, removed merchants)

        Returns
        -------
            Callable
                The function to be called to display the requested information
            None
                If an invalid item is requested
        """
        user_response: str = input("Enter 'p' to see product removal history, or 'm' to see merchant removal history. ")
        match user_response:
            case 'p' | 'P':
                return self.display_product_removal_history
            case 'm' | 'M':
                return self.display_merchant_removal_history
            case _:
                print("Invalid choice")
                return None
        

    def display_main_menu_and_get_user_input(self):
        should_continue: bool = True
        while (should_continue):
            controls_table_headers: list[str] = ["Review Reports", "Remove Product", "Remove Seller", "History", "Sign out"]
            controls_table_entries: list[list[str]] = [['v', 'a', 's', 'h', 'x']]
            print(tabulate(controls_table_entries, headers=controls_table_headers, tablefmt='simple'))
            user_response: str = ""
            while (user_response == ""):
                user_response = input()
                match user_response:
                    case 'v':
                        # Review Reports
                        self.display_unreviewed_reports_for_unreviewed_products()
                        next_function: Callable | None = self.get_user_choice_in_response_to_display_of_unreviewed_reports()
                        if (next_function != None):
                            next_function()
                    case 'a':
                        # Remove product
                        product_id = self.get_product_removal_input()
                        if (self.remove_product(product_id)):
                            print("Product successfully removed.")
                        else:
                            print("Something went wrong.")
                    case 's':
                        # Remove seller
                        merchant_id = self.get_merchant_removal_input()
                        if (self.remove_merchant(merchant_id)):
                            print("Merchant successfully removed")
                        else:
                            print("Something went wrong.")
                    case 'h':
                        # See removal history
                        display_function: Callable | None = self.get_history_function_based_on_input()
                        if (display_function != None):
                            display_function()
                    case 'x':
                        # Sign out
                        should_continue = False
                        return
                    case _:
                        user_response = ""

    def begin_interaction(self):
        print(f"Welcome, {self._moderator_info.first_name} {self._moderator_info.last_name}.")
        self.display_main_menu_and_get_user_input()

    