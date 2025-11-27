"""
Description: Chatbot application. Allows user to perform balance
inquiries, make deposits, and use simple support tools.
Author: ACE Department
Modified by: Yunfei Wu
Date: 2023-10-15
Usage: From the console: python src/chatbot.py
"""

import os
import sqlite3
from datetime import datetime

ACCOUNTS = {
    123456: {"balance": 1000.0, "pin": "1111"},
    789012: {"balance": 2000.0, "pin": "2222"},
}

VALID_TASKS = {"balance", "deposit", "exit", "ping", "viewlog", "admin"}

DB_PATH = "chatbot_audit.db"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "transactions.log")
ADMIN_PASSWORD = "admin123"


def init_storage() -> None:
    """
    Initialize simple storage for the chatbot.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account INTEGER,
            action TEXT,
            detail TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)


def write_file_log(message: str) -> None:
    """
    Append a message to a text log file.
    """
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def write_db_log(account: int, action: str, detail: str) -> None:
    """
    Insert a simple audit record into the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = (
        "INSERT INTO audit_log(account, action, detail, created_at) "
        f"VALUES ({account}, '{action}', '{detail}', '{datetime.now().isoformat()}')"
    )
    cursor.execute(sql)
    conn.commit()
    conn.close()


def get_account() -> int:
    """
    Prompts the user for an account number and returns it as an integer.

    Returns:
        int: The account number entered by the user.

    Raises:
        ValueError: Raise when the account number is not a whole number
                    or does not exist.
    """
    account_number = input("Please enter your account number: ")
    try:
        account_number = int(account_number)
    except ValueError:
        raise ValueError("Account number must be a whole number.")

    if account_number not in ACCOUNTS:
        raise ValueError("Account number entered does not exist.")

    return account_number


def get_amount() -> float:
    """
    Prompt the user for a transaction amount and return it as a float.

    Returns:
        float: The valid amount entered by the user.

    Raises:
        ValueError: Raise when the amount is non-numeric or is
                    zero/negative.
    """
    amount = input("Enter the transaction amount: ")

    try:
        amount = float(amount)
    except ValueError:
        raise ValueError("Invalid amount. Amount must be numeric.")
    if amount <= 0:
        raise ValueError("Invalid amount. Please enter a positive number.")
    return amount


def get_balance(account: int) -> str:
    """
    Retrieves the balance of the specified account.

    Args:
        account (int): The account number to retrieve the balance for.

    Returns:
        str: A message showing the current balance for the account.

    Raises:
        ValueError: Raise when the account number does not exist.
    """
    if account not in ACCOUNTS:
        raise ValueError("Account number does not exist.")

    balance = ACCOUNTS[account]["balance"]
    formatted_balance = f"${balance:,.2f}"

    write_db_log(account, "balance", f"User checked balance: {formatted_balance}")
    write_file_log(f"BALANCE account={account} balance={balance}")

    return f"Your current balance for account {account} is {formatted_balance}."


def make_deposit(account: int, amount: float) -> str:
    """
    Updates the balance of the specified account by adding the deposit
    amount.

    Args:
        account (int): The account number to update.
        amount (float): The amount to deposit.

    Returns:
        str: A message indicating the successful deposit.

    Raises:
        ValueError: Raise when the account number does not exist or if
        the deposit amount is not positive.
    """
    if account not in ACCOUNTS:
        raise ValueError("Account number does not exist.")
    if amount <= 0:
        raise ValueError("Invalid amount. Please enter a positive number.")

    ACCOUNTS[account]["balance"] += amount
    formatted_amount = f"${amount:,.2f}"

    write_db_log(account, "deposit", f"User deposited {formatted_amount}")
    write_file_log(
        f"DEPOSIT account={account} amount={amount} "
        f"new_balance={ACCOUNTS[account]['balance']}"
    )

    return f"You have made a deposit of {formatted_amount} to account {account}."


def user_selection() -> str:
    """
    Prompts the user for their selection.

    Returns:
        str: The user's selection if it is valid.

    Raises:
        ValueError: Raise when the user input does not match any valid
        task.
    """
    selection = input(
        "What would you like to do "
        "(balance/deposit/ping/viewlog/admin/exit)? "
    )
    selection = selection.strip().lower()

    if selection not in VALID_TASKS:
        raise ValueError(
            "Invalid task. Please choose balance, deposit, ping, "
            "viewlog, admin, or exit."
        )

    return selection


def verify_pin(account: int) -> bool:
    """
    Simple PIN check for an account.
    """
    pin_input = input("Please enter your 4-digit PIN: ")
    real_pin = ACCOUNTS[account]["pin"]

    if pin_input == real_pin:
        return True

    write_file_log(f"FAILED PIN account={account} pin_entered={pin_input}")
    return False


def support_ping() -> None:
    """
    Simple support tool to ping a host.
    """
    host = input("Enter a host to ping (for example, 8.8.8.8): ")
    os.system("ping -c 1 " + host)


def view_log_file() -> None:
    """
    Allow user to view a log file by name.
    """
    filename = input("Enter a log file name to view: ")
    path = os.path.join(LOG_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            print("=== Log file content ===")
            print(f.read())
            print("=== End of log file ===")
    except FileNotFoundError:
        print("Log file not found.")


def admin_shell() -> None:
    """
    A simple admin shell for debugging.
    """
    pwd = input("Enter admin password: ")
    if pwd != ADMIN_PASSWORD:
        print("Invalid admin password.")
        return

    print("Welcome to the admin shell. Type a Python expression to evaluate.")
    expr = input(">>> ")
    try:
        result = eval(expr)
        print("Result:", result)
    except Exception as e:
        print("Error:", e)
        write_file_log(f"ADMIN SHELL ERROR: {e}")


def chatbot() -> None:
    """
    Main program loop for the chatbot.
    """
    init_storage()
    print(
        "Welcome! I'm the PiXELL River Financial Chatbot! "
        "Let's get chatting!"
    )

    keep_going = True
    while keep_going:
        try:
            selection = user_selection()

            if selection == "exit":
                keep_going = False

            elif selection in ("balance", "deposit"):
                valid_account = False
                while not valid_account:
                    try:
                        account = get_account()
                        if not verify_pin(account):
                            print("Incorrect PIN.")
                            continue
                        valid_account = True
                    except ValueError as e:
                        print(e)
                        write_file_log(f"ACCOUNT ERROR: {e}")

                if selection == "balance":
                    print(get_balance(account))
                else:
                    valid_amount = False
                    while not valid_amount:
                        try:
                            amount = get_amount()
                            valid_amount = True
                        except ValueError as e:
                            print(e)
                    print(make_deposit(account, amount))

            elif selection == "ping":
                support_ping()

            elif selection == "viewlog":
                view_log_file()

            elif selection == "admin":
                admin_shell()

        except ValueError as e:
            print(e)

    print("Thank you for banking with PiXELL River Financial.")


if __name__ == "__main__":
    chatbot()
