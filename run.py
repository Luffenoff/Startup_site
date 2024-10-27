from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "test") 

@app.route("/")
def home():
    return render_template("base.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin123":
            flash("Вход успешен", "success")
            return redirect(url_for('home'))
        else:
            flash("Неверный логин или пароль", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        flash("Регистрация пройдена! Пожалуйста войдите.", "success")
        return redirect(url_for('login'))  
    return render_template("register.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        flash("Сообщение для сброса пароля отправлено на вашу почту", "success")
        return redirect(url_for('login'))  
    return render_template("forgot_password.html")

if __name__ == "__main__":
    app.run(debug=True)
