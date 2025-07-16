import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    old_portfolio = db.execute("SELECT stock, owned, price, total FROM purchases WHERE users_id = ?",
                               session["user_id"])  # Returns a list of dictionary

    # Loop through all stocks currently owned by a user
    for row in old_portfolio:

        # Get the lookup of each stock symbol by row
        result = lookup(row["stock"])

        # Get their current market price
        current_price = round(float(result["price"]), 2)

        # Get the price of that stock * the number the user owns
        current_total = current_price * int(row["owned"])

        # Update the market price in the purchases table shown in index
        db.execute("UPDATE purchases SET price = ?, total = ? WHERE stock = ? AND users_id = ?",
                   current_price, current_total, result["symbol"], session["user_id"])

    portfolio = db.execute("SELECT stock, owned, price, total FROM purchases WHERE users_id = ?",
                           session["user_id"])  # Returns a list of dictionary

    # Display total value of stocks price owned and remaining cash balance together on another table
    stockpile = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

    # Initialize n to 0
    total_holdings = 0

    # DO MATH TO CALCULATE THE TOTAL PRICE OF ALL THE STOCKS THE USER OWNS
    for item in portfolio:
        # Stores the current value of total in current_item
        current_item = round(float(item["total"]), 2)

        # Take whatever total we’ve already counted (n), add the current stock’s total value, and store the new sum back into n.
        total_holdings = round(float(total_holdings + current_item), 2)

    rows = db.execute("SELECT * FROM stonks WHERE users_id = ?", session["user_id"])
    if len(rows) == 0:
        db.execute("INSERT INTO stonks (users_id, overall_total) VALUES (?, ?)",
                   session["user_id"], total_holdings)
    else:
        db.execute("UPDATE stonks SET overall_total = ? WHERE users_id = ?",
                   total_holdings, session["user_id"])

    stonks = db.execute("SELECT overall_total FROM stonks WHERE users_id = ?", session["user_id"])

    return render_template("index.html", portfolio=portfolio, stockpile=stockpile, stonks=stonks)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # When submitted via POST, purchase the stock so long as the user can afford it
    if request.method == "POST":

        # Ask for a symbol and number of shares
        stocks = request.form.get("symbol")
        if not request.form.get("symbol"):
            return apology("Please input stock symbol", 400)

        amount = request.form.get("shares")
        if not request.form.get("shares"):
            return apology("Please input number of stocks", 400)

        result = lookup(stocks)  # Returns a dictionary containing name, price, and symbol

        # Check for valid input
        if not result:
            return apology("Quote symbol stock result not found", 400)

        # Ensure user has enough cash to purchase stock and number of shares
        math = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        c = float(math[0]["cash"])  # Current cash the user has
        p = float(result["price"])  # Current market price of the stock

        try:
            shares = int(amount)  # Integer number of how many stocks the user wants to own
        except (ValueError, TypeError):
            return apology("Please input a valid whole number of shares.", 400)

        if shares < 1:
            return apology("Please input a number greater than zero.", 400)

        cash = round(c, 2)
        price = round(p, 2)
        total = round(price * shares, 2)

        new_cash = round((cash - total), 2)

        # If the user doesnt have enough cash, return an apology
        if new_cash < 0:
            return apology("Invalid cash amount", 400)

        # Run SQL statement on database to purchase a stock

        rows = db.execute("SELECT * FROM purchases WHERE stock = ? AND users_id = ?",
                          stocks, session["user_id"])
        if len(rows) == 0:
            db.execute("INSERT INTO purchases (users_id, stock, owned, price, total) VALUES(?, ?, ?, ?, ?)",
                       session["user_id"], stocks, shares, price, total)
        else:
            # integer number of current total owned of the selected stock
            owd = int(rows[0]["owned"])
            # decimal number of current total price of the selected stock
            tol = round(float(rows[0]["total"]), 2)

            owd = owd + shares  # updated current owned of the selected stock
            tol = owd * p  # updated current total of the selected stock

            db.execute("UPDATE purchases SET owned = ?, total = ? WHERE STOCK = ? AND users_id = ?",
                       owd, tol, stocks, session["user_id"])

        # Update cash to reflect purchased stock
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])

        # Run statements to update transactions that a stock was bought
        action = "Bought"
        db.execute("INSERT INTO transactions (users_id, stock, action, owned, price) VALUES(?, ?, ?, ?, ?)",
                   session["user_id"], stocks, action, shares, p)

        return redirect("/")

    # When requested via GET, display a form to buy a stock
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Display a table with a history of all transactions
    hstry = db.execute(
        "SELECT stock, action, owned, price, timestamp FROM transactions WHERE users_id = ?", session["user_id"])

    return render_template("history.html", hstry=hstry)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # When submitted via POST, lookup the stock symbol by calling the lookup function and display the results
    if request.method == "POST":

        quote_symbol = request.form.get("symbol")
        # If field is left blank return an apology
        if not request.form.get("symbol"):
            return apology("Please input quote symbol", 400)

        result = lookup(quote_symbol)  # Returns a dictionary containing name, price, and symbol
        if not result:
            # If symbol doesnt exist, return an apology
            return apology("Quote symbol stock result not found", 400)

        return render_template("quoted.html", result=result)

    # When requested via GET, display a form that requests a stock quote
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # When submitted via POST,
    if request.method == "POST":

        # SERVER SIDE VALIDATION

        # If any field is left blank, return an apology
        if not request.form.get("username") or not request.form.get("password"):
            return apology("Please input username or password", 400)

        # If password and confirmation does not match, return an apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password does not match", 400)

        # Store the username and password in a variable
        username = request.form.get("username")
        unhashed_password = request.form.get("password")

        # If the username is already taken, return an apology
        username_checker = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(username_checker) > 0:  # Checks if the returned rows of username_checker has more than a value of 0 (means theres already someone with that username)
            return apology("username already taken", 400)

        # Use generate_password_hash to generate a hash of that password
        password = generate_password_hash(unhashed_password)

        # Add the new approved user to the database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, password)

    # Logging the user in
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Forget any user_id
        session.clear()

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Sends the user to the homepage
        return redirect("/")

    # When requested via GET, display registration form
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # When form is submitted via POST, check for errors and sell the specified number of shares of stocks and update the users cash
    options = db.execute("SELECT stock FROM purchases WHERE users_id = ?", session["user_id"])

    if request.method == "POST":

        # SERVER SIDE VALIDATION
        sell_symbol = request.form.get("symbol")

        validation = lookup(sell_symbol)  # Returns stock name, price, and symbol
        if not validation:
            return apology("Quote symbol stock result not found", 400)

        n = request.form.get("shares")

        try:
            amount_request = int(n)
        except (ValueError, TypeError):
            return apology("Invalid share amount", 400)

        checking = db.execute("SELECT stock FROM purchases WHERE users_id = ?", session["user_id"])
        # Check if the user has those stocks currently owned
        for item in checking:
            symbol_check = item["stock"]

            if sell_symbol == symbol_check:  # If a match is FOUND break out of the loop and DOES NOT EXECUTE THE ELSE BLOCK
                break  # If a match is NOT FOUND the else block outside the loop will BE EXECUTED
        else:
            return apology("Invalid stock", 400)

        # Check if the user has those number of stocks shares
        selling_check = db.execute(
            "SELECT owned FROM purchases WHERE stock = ? AND users_id = ?", sell_symbol, session["user_id"])

        amount_check = int(selling_check[0]["owned"])
        if amount_request > amount_check:
            return apology("Invalid stocks owned", 400)

            # END OF SERVER SIDE VALIDATION

        selling = db.execute(
            "SELECT owned, price, total FROM purchases WHERE stock = ? AND users_id = ?", sell_symbol, session["user_id"])
        user_profile = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        # Subtract the total shares held to the amount the user wants to sell
        current_owned = int(selling[0]["owned"])  # Number of Stocks held
        current_owned = current_owned - amount_request  # Current number of stocks held by the user

        # Update the users total price for that stock using real time stock prices
        market_price = round(float((validation["price"])), 2)  # Current market price per stock
        # Total price of stock reflective of the current market price
        owned_price = market_price * int(selling[0]["owned"])

        # Update the user's purchases table prices and total for that stock
        sell_gain = market_price * amount_request  # Price gained after selling
        # Current price user owns of that stock in the database after selling
        owned_price = current_owned * market_price

        # Current amount of cash held by the user
        sell_gain = sell_gain + round(float(user_profile[0]["cash"]), 2)

        # Update the user's total cash balance and the current total price held after calculating the current market price
        if current_owned > 0:
            db.execute("UPDATE purchases SET owned = ?, price = ?, total = ? WHERE stock = ? AND users_id = ?",
                       current_owned, market_price, owned_price, sell_symbol, session["user_id"])
        else:
            db.execute("DELETE FROM purchases WHERE stock = ? AND users_id = ?",
                       sell_symbol, session["user_id"])

        # Calculate the total amount of all the UPDATED prices for all the stocks they currently owned after selling
        updated_total = db.execute(
            "SELECT total FROM purchases WHERE users_id = ?", session["user_id"])

        total_holdings = 0
        for item in updated_total:
            current_item = round(float(item["total"]), 2)
            total_holdings = round(float(total_holdings + current_item), 2)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", sell_gain, session["user_id"])
        db.execute("UPDATE stonks SET overall_total = ? WHERE users_id = ?",
                   total_holdings, session["user_id"])

        # Update transasctions to reflect that a stock was sold
        action = "Sold"
        db.execute("INSERT INTO transactions (users_id, stock, action, owned, price) VALUES(?, ?, ?, ?, ?)",
                   session["user_id"], sell_symbol, action, n, market_price)

        return redirect("/")

    # When requested via GET, display a form to sell a stock
    else:
        return render_template("sell.html", options=options)


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    # If request method post
    if request.method == "POST":

        # Add a form to state how much cash the user wants to deposit
        a = request.form.get("amount")
        if not request.form.get("amount"):
            return apology("Please input a valid amount", 400)

        cash_amount = round(float(a), 2)
        if cash_amount < 1:
            return apology("Please input a valid amount", 400)

        # Update their current cash balance to reflect on how much they deposited
        b = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

        updated_cash = round(float(b[0]["cash"]), 2)

        updated_cash = round(float(cash_amount + updated_cash), 2)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, session["user_id"])

        return redirect("/")

    # Else if request method get
    else:
        return render_template("deposit.html")
