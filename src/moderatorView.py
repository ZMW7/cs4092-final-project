from commonTypes import *
import psycopg
from psycopg import sql
from tabulate import tabulate

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
                    DELETE FROM sellers WHERE id = %s
                """),
                (merchant_id,)
            )
            self.cursor.fetchall()
        except:
            return False
        # Deleting all products
        self.cursor.execute(
            sql.SQL("""
                DELETE FROM products WHERE seller_id = %s
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
        self.cursor.fetchall()

        #  Inserting into 'product_removals' table
        product_removals_insertions: list[tuple[int, int]] = [ (self._moderator_info.id, merchant_id, deleted_product) for deleted_product in deleted_products ]
        self.cursor.executemany(
            sql.SQL("""
                INSERT INTO product_removals (removed_by, seller_id, product_id) VALUES
                (%s, %s, %s)
            """),
            product_removals_insertions
        )
        self.cursor.fetchall()
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
                    DELETE FROM products WHERE id = %s
                    RETURNING id, seller_id
                """),
                (product_id,)
            )
        except:
            return False
        removed_product_id, seller_id = self.cursor.fetchall()[0]
        self.cursor.execute(
            sql.SQL("""
                INSERT INTO product_removals (removed_by, seller_id, product_id) VALUES
                (%s, %s, %s)
            """),
            (self._moderator_info.id, seller_id, removed_product_id)
        )
        self.connection.commit()
        return True

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
        pass

    def handle_report_review_input(self):
        pass

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

    def display_main_menu_and_get_user_input(self):
        should_continue: bool = True
        while (should_continue):
            controls_table_headers: list[str] = ["View Unreviewed Reports", "Remove Product", "Remove Seller", "History", "Sign out"]
            controls_table_entries: list[list[str]] = [['v', 'a', 's', 'h', 'x']]
            print(tabulate(controls_table_entries, headers=controls_table_headers, tablefmt='simple'))
            user_response: str = ""
            while (user_response == ""):
                user_response = input()
                match user_response:
                    case 'v':
                        # View unreviewed reports
                        pass
                    case 'a':
                        # Remove product
                        product_id = self.get_product_removal_input()
                        self.remove_product(product_id)
                    case 's':
                        # Remove seller
                        merchant_id = self.get_merchant_removal_input()
                        self.remove_merchant(merchant_id)
                    case 'h':
                        # See removal history
                        pass
                    case 'x':
                        # Sign out
                        should_continue = False
                        return
                    case _:
                        user_response = ""

    def begin_interaction(self):
        print(f"Welcome, {self._moderator_info.first_name} {self._moderator_info.last_name}.")
        pass

    