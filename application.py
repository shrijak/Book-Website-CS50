import os
import requests

from flask import Flask, request, render_template, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from imports import main

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.static_folder = 'static'
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# main

name = ''
id = 0


@ app.route("/")
def index():
    global name
    global id
    name = ''
    id = 0
    return render_template("index.html")


@ app.route("/home", methods=["POST", "GET"])
def home():
    global name
    global id
    if request.method == "POST":
        if request.form["Click"] == "Register":
            name = request.form.get("name")
            dob = request.form.get("dob")
            password = request.form.get("passsign")
            email = request.form.get("email")
            gender = request.form["gender"]
            db.execute("INSERT INTO users (email, name, password, dob, gender) VALUES (:email, :name, :password, :dob, :gender)", {
                       'email': email, 'name': name, 'password': password, 'dob': dob, 'gender': gender})
            db.commit()
            user = db.execute("SELECT * FROM users WHERE email=:email AND password=:password", {
                              "email": email, "password": password}).fetchone()
            name = user.name
            id = user.id
            return render_template("home.html", name=name)

        elif request.form["Click"] == "Login":
            email = request.form.get("user")
            password = request.form.get("pass")
            if db.execute("SELECT * FROM users WHERE email=:email AND password=:password", {"email": email, "password": password}).rowcount == 0:
                return render_template("error.html", message="User doesn't exist! OR Wrong Password")
            else:
                user = db.execute("SELECT * FROM users WHERE email=:email AND password=:password", {
                                  "email": email, "password": password}).fetchone()
                name = user.name
                id = user.id
                return render_template("home.html", name=name)

        if request.form["Click"] == "Search":
            book = request.form.get("book")
            if request.form["Type"] == "isbn":
                books = db.execute(
                    "SELECT * FROM books WHERE isbn LIKE :book ", {"book": '%' + book + '%'})
            elif request.form["Type"] == "title":
                books = db.execute(
                    "SELECT * FROM books WHERE title LIKE :book ", {"book": '%' + book + '%'})
            elif request.form["Type"] == "author":
                books = db.execute(
                    "SELECT * FROM books WHERE author LIKE :book ", {"book": '%' + book + '%'})
            elif request.form["Type"] == "year":
                books = db.execute(
                    "SELECT * FROM books WHERE year LIKE :book ", {"book": '%' + book + '%'})
            return render_template("home.html", name=name, books=books)
    elif request.method == "GET":
        return render_template("home.html", name=name)


@ app.route("/book/<string:book_isbn>", methods=["POST", "GET"])
def onebook(book_isbn):
    global id
    myreview = []
    book = db.execute("SELECT * FROM books WHERE isbn=:book ",
                      {'book': book_isbn}).fetchone()

    if request.method == "POST":
        review = request.form.get("review")
        rating = request.form.get("rating")
        db.execute("INSERT INTO reviews (id,isbn,review,rating) VALUES (:id,:isbn,:review,:rating) ", {
                   "id": id, "isbn": book_isbn, "review": review, "rating": rating})
        db.commit()

    if db.execute("SELECT * FROM reviews WHERE id = :id AND isbn = :isbn ", {"id": id, "isbn": book_isbn}).rowcount == 0:
        flag = 0

    else:
        flag = 1
        myreview = db.execute("SELECT * FROM reviews WHERE id = :id AND isbn = :isbn ", {
            "id": id, "isbn": book_isbn}).fetchone()

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "VLpikvS7CHA1BWib89E1Cw", "isbns": book_isbn})
    return render_template("book.html", book=book, flag=flag, myreview=myreview, res=res.json())


@ app.route("/api/<string:book_isbn>")
def book_api(book_isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :book ",
                      {"book": book_isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid isbn"}), 422

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "VLpikvS7CHA1BWib89E1Cw", "isbns": book_isbn})
    data = res.json()
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": data['books'][0]['work_ratings_count'],
        "average_score": data['books'][0]['average_rating']
    })
