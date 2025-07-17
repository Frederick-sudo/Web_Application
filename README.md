Project Description:

A full-stack web application that simulates a stock trading platform that was developed as part of Harvard University’s CS50x course. This web application allows users to manage a mock stock portfolio using real time data through API.

Features:
User authentication with a hashing for password for added security measures.
Through IEX API, users can buy and sell stocks using REAL TIME prices.
Overview of portfolio with current market valuations.
Tracks history of ALL transactions.
Uses SQLite database to store data.

How each technology was used:
Python/Flask
-Built the core backend of the web application
-Manages user sessions, stock trading logic, and authentication
-Equipped with server side validation
-Services dynamic HTML web pages via routes

SQLite
-Stores persistent data of user accounts and their hashed passwords, stock purchase and sell history, and real time portfolio valuation
-Wrote SQL queries in python to update and fetch necessary data

HTML (with Jinja2)
-Built frontend of the web app
-Embedded with dynamic data from Flask

CSS
-Provides basic styling for tables, forms, and navigation through bootstrap

IEX API
-Handles real-time stock price fetching using API request from the backend code from Python
	
How to run:
Clone the repository (https://github.com/Frederick-sudo/cs50-finance)
Set up a virtual environment (python -m venv venv source venv/bin/activate # On Windows, use venv\Scripts\activate)
Install dependencies (pip install -r requirements.txt)
Set your IEX API key ina “.env” file or as an environment variable
Run the flask app (flask run)
Visit the app in your browser (http://127.0.0.1:5000/) (in your browser after running the Flask app locally.

Project Background
Built as a core project in **CS50x: Computer Science Course** from Harvard University, this app simulates real-world stock trading platforms, demonstrating full-stack web development skills.
