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

    def remove_merchant(merchant_id: int):
        pass

    def remove_product(product_id: int):
        pass

    def get_number_of_product_removals_for_merchant(self, seller_id: int):
        pass

    def display_previously_reviewed_reports(self):
        pass

    def display_unreviewed_reports_for_listed_products(self):
        pass

    def handle_report_review_input(self):
        pass

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
                        pass
                    case 's':
                        # Remove seller
                        pass
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

    