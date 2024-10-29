from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
import os
from dotenv import load_dotenv
from database import create_table, add_user, update_user, get_user, get_db_connection


load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "test")


create_table()


@app.route("/")
def home():
    user_authenticated = 'logged_in' in session 
    return render_template("base.html", user_authenticated=user_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user(username, password)
        if user:
            session['logged_in'] = True 
            session['user_id'] = user['id']
            flash("Вход успешен", "success")
            return redirect(url_for('home'))
        else:
            flash("Неверный логин или пароль", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nickname = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if add_user(nickname, email, password):
            flash("Регистрация пройдена! Пожалуйста, войдите.", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка регистрации. Попробуйте другой адрес электронной почты.", "error")
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
    response.set_cookie('cookie_consent', 'true', max_age=30*24*60*60) 
    flash("Вы согласились на использование куки.", "success")
    return response


@app.route("/profile", methods=["GET"])
def profile():
    if 'logged_in' not in session or 'user_id' not in session: 
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user is None:
        flash("Пользователь не найден.", "error")
        return redirect(url_for('login'))
    registration_date = user['registration_date']
    return render_template("profile.html", nickname=user['nickname'], email=user['email'], registration_date=registration_date)


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if 'logged_in' not in session:  
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    nickname = request.form["nickname"]
    profile_image = request.files.get("profile_image")
    update_user(user_id, nickname)
    if profile_image:
        profile_image_path = os.path.join("static/images", profile_image.filename)
        profile_image.save(profile_image_path)
    flash("Изменения сохранены", "success")
    return redirect(url_for('profile'))


@app.route("/logout")
def logout():
    session.pop('logged_in', None) 
    flash("Вы вышли из системы", "success")
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
