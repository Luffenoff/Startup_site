from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "test")

# Создание базы данных (если ее еще нет)
def init_db():
    conn = sqlite3.connect('cookies.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cookie_consent (
            id INTEGER PRIMARY KEY,
            consent BOOLEAN NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    user_authenticated = 'logged_in' in session  # Проверка аутентификации
    return render_template("base.html", user_authenticated=user_authenticated)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin123":
            session['logged_in'] = True  # Устанавливаем флаг входа
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
        flash("Регистрация пройдена! Пожалуйста, войдите.", "success")
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        flash("Сообщение для сброса пароля отправлено на вашу почту", "success")
        return redirect(url_for('login'))
    return render_template("forgot_password.html")

@app.route('/accept_cookies')
def accept_cookies():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('cookie_consent', 'true', max_age=30*24*60*60)  # Согласие на 30 дней

    # Сохранение согласия в базе данных
    conn = sqlite3.connect('cookies.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO cookie_consent (consent) VALUES (?)', (True,))
    conn.commit()
    conn.close()

    flash("Вы согласились на использование куки.", "success")
    return response

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'logged_in' not in session:  # Проверка аутентификации
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))

    if request.method == "POST":
        nickname = request.form["nickname"]
        profile_image = request.files.get("profile_image")

        # Здесь можно добавить логику для сохранения изображений и обновления профиля

        flash("Изменения сохранены", "success")
        return redirect(url_for('profile'))

    # Здесь нужно получить дату регистрации пользователя
    registration_date = datetime.now().strftime("%Y-%m-%d")  # Текущая дата
    nickname = "Ваш никнейм"  # Замените на данные из базы
    email = "ваша_почта@example.com"  # Замените на данные из базы

    return render_template("profile.html", nickname=nickname, email=email, registration_date=registration_date)

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if 'logged_in' not in session:  # Проверка аутентификации
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))

    nickname = request.form["nickname"]
    profile_image = request.files.get("profile_image")

    # Здесь можно добавить логику для сохранения изображений и обновления профиля

    flash("Изменения сохранены", "success")
    return redirect(url_for('profile'))

@app.route("/logout")
def logout():
    session.pop('logged_in', None)  # Удаление пользователя из сессии
    flash("Вы вышли из системы", "success")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
