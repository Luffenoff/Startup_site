from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
from flask_caching import Cache
import os
import requests
import logging
from dotenv import load_dotenv
from database import create_table, add_user, update_user, get_user, get_db_connection
from functools import wraps 
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "test")
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


create_table()


@app.route("/")
def home():
    user_authenticated = 'logged_in' in session 
    return render_template("base.html", user_authenticated=user_authenticated)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/logs.log", encoding='UTF-8'),
        logging.StreamHandler()
    ]
)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session.get('role') != 'admin':
            flash('У вас нет доступа к этой странице.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def get_user_location(ip_address):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'success':
            return {
            'city': data["city"],
            'country': data['country'],
            'provider': data['isp']
            }
    except Exception as e:
        logging.error(f"Не удалось получить данные о местоположении: {e}")
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user(username, password)
        if user:
            session['logged_in'] = True 
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash("Вход успешен", "success")
            ip_address = request.remote_addr
            logging.info(f"Пользователь {username} вошел в систему с IP {request.remote_addr}")
            location_data = get_user_location(ip_address)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users
                    SET last_active = ?, ip_address = ?, city = ?, country = ?, provider = ?
                    WHERE id = ?
                ''', (
                    datetime.now(),
                    ip_address,
                    location_data['city'] if location_data else None,
                    location_data['country'] if location_data else None,
                    location_data['provider'] if location_data else None,
                    user['id']
                ))
                conn.commit()

            return redirect(url_for('home'))
        else:
            flash("Неверный логин или пароль", "error")
            logging.warning(f"Неудачная попытка входа для {username}")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nickname = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if nickname and password and email:
            if add_user(nickname, email, password):
                flash("Регистрация пройдена! Пожалуйста, войдите.", "success")
                logging.info(f"Новый пользователь зарегистрирован: {nickname}, Email: {email}")
                return redirect(url_for('login'))
            else:
                flash("Ошибка регистрации. Попробуйте другой адрес электронной почты.", "error")
        else:
            flash("Пожалуйста, заполните все поля.", "error")
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
    if nickname:
        update_user(user_id, nickname)
    if profile_image:
        profile_image_path = os.path.join("static/images", profile_image.filename)
        profile_image.save(profile_image_path)
    flash("Изменения сохранены", "success")
    return redirect(url_for('profile'))


@app.route("/admin_dashboard")
def admin_dashboard():
    if 'logged_in' not in session or 'user_id' not in session:
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", users=users)


@app.route("/change_role/<int:user_id>", methods=["POST"])
def change_role(user_id):
    if 'logged_in' not in session or 'user_id' not in session:
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))
    new_role = request.form["role"]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
        conn.commit()
        conn.close()
    flash("Роль пользователя изменена", "success")
    return redirect(url_for('admin_dashboard'))


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if 'logged_in' not in session or 'user_id' not in session:
        flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    logging.info(f"Пользователь {session['user_id']} удалил пользователя с id {user_id}")
    flash("Пользователь удален", "success")
    return redirect(url_for('admin_dashboard'))


@app.route("/site_stats")
def site_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    return render_template("index.html", user_count=user_count)


@app.route('/add_startup', methods=['GET', 'POST'])
def add_startup():
    if 'user_id' not in session:
        flash("Пожалуйста, войдите в систему.", "error")
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image = request.files['image']
        user_id = session.get('user_id')
        startup_uuid = str(uuid.uuid4())
        image_path = None
        if image:
            image_path = os.path.join('static/images', image.filename)
            image.save(image_path)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO startups (name, description, image_path)
                           VALUES (?, ?, ?)
                           ''', (name, description, image_path))
            conn.commit()
            
            startup_id = cursor.lastrowid
            
            cursor.execute('''
                           INSERT INTO startup_submissions (startup_id, user_id, moderation_status)
                           VALUES (?, ?, 'На модерации')
                           ''', (startup_id, user_id))
            conn.commit()
        logging.info(f"Пользователь {session['user_id']} добавил стартап: {name}, описание; {description}")
        flash("Стартап успешно добавлен!", "success")
        return redirect(url_for('view_startups'))
    return render_template('add_startup.html')


@app.route('/view_startups')
def view_startups():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM startups')
    startups = cursor.fetchall()
    conn.close()
    return render_template('view_startups.html', startups=startups)
        

@app.route("/logout")
def logout():
    user_id = session.get('user_id')
    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT nickname FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            nickname = user[0]
            logging.info(f"Пользователь {nickname} вышел из системы")
        else:
            nickname = "Неизвестный пользователь"
    else:
        nickname = "Неизвестный пользователь"
    session.pop('logged_in', None)
    session.pop('user_id', None)
    logging.info(f"Пользователь {nickname} вышел из системы.")
    flash("Вы вышли из системы", "success")
    return redirect(url_for('home'))


@app.route('/moderation', methods=['GET'])
@admin_required
def moderate_startup():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM startups")
    startups = cursor.fetchall()
    conn.close
    return render_template('moderation.html', startups=startups)


@app.route('/moderate_startup', methods=['GET'])
@admin_required
def moderate_startup_page():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ss.id, s.name, s.description, s.image_path, ss.moderation_status
            FROM startup_submissions ss
            JOIN startups s ON ss.startup_id = s.id
            WHERE ss.moderation_status = 'На модерации'
        ''')
        startups = cursor.fetchall()
    
    startups_data = [{
        'id': startup[0],
        'name': startup[1],
        'description': startup[2],
        'publication_date': startup[3],
        'status': startup[4]
    } for startup in startups]

    return render_template('moderation.html', startups=startups_data)



@app.route("/moderate_startup/<int:startup_id>/<status>", methods = ['POST'], endpoint='moderate_startup_status')
@admin_required
def moderate_startup_status(startup_id, status):
    valid_statuses = ['Опубликовано', 'На модерации', 'Отклонено']
    if status not in valid_statuses:
        flash("Некорректно", "error")
        return redirect(url_for('moderate_startup_page'))
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT * FROM startup_submissions WHERE startup_id = ?
                       ''', (startup_id,))
        startup = cursor.fetchone()
        if not startup:
            flash("Карточка с таким id не найден.", "error")
            return redirect(url_for('moderate_startup_page'))
        cursor.execute('''
                    UPDATE startup_submissions
                    SET moderation_status = ?
                    WHERE startup_id = ?
                    ''', (status, startup_id))
        conn.commit()
    logging.info(f"Стартап ID {startup_id} статус изменил на {status}")
    flash(f"Статус стартапа изменен на {status}.", "success")
    return redirect(url_for('moderate_startup_page'))


@app.route('/view_startup/<int:startupid>')
def view_startup(startupid):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT * FROM startups WHERE id = ?
                       ''', (startupid,))
        startup = cursor.fetchone()

        if startup:
            cursor.execute('''
                           SELECT * FROM startup_submissions WHERE startup_id = ? AND moderation_status = 'Принят'
                           ''', (startupid,))
            submission = cursor.fetchone()

            if submission:
                return render_template('view_startup.html', startup=startup)
            else:
                flash("Этот стартап еще не прошел модерацию.", "warning")
                return redirect(url_for('view_startups'))
        else:
            flash("Стартап не найден.", "error")
            return redirect(url_for('view_startups'))
    

@app.route('/approve_startup/<int:startup_id>', methods=['POST'])
@admin_required
def approve_startup(startup_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("UPDATE startups SET moderation_status = 'Опубликовано' WHERE startup_id = ?", (startup_id,))
        conn.commit()
        flash("Стартап одобрен!", "success")
        return redirect(url_for('moderate_startup'))
        

@app.route('/reject_startup/<int:startup_id>', methods=['POST'])
@admin_required
def reject_startup(startup_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE startups SET moderation_status = 'Отклонено' WHERE startup_id = ?", (startup_id,))
    flash("Стартап отклонен.", "error")
    return redirect(url_for('moderate_startup'))
                       



@app.route("/faq", methods = ['GET', 'POST'])
def faq():
    if request.method == "POST":
        if 'logged_in' not in session:
            flash("Пожалуйста, войдите в аккаунт")
            return redirect(url_for('login'))
        question = request.form.get("question")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO faq_questions (user_id, question) VALUES (?, ?)',
                       (session['user_id'], question))
            conn.commit()
        flash("Ваш запрос был отправлен", "success")
        return redirect(url_for('faq'))
    return render_template("faq.html")
    

##def main():
    ##home()
    ##admin_required
    ##login()
    


if __name__ == "__main__":
    app.run(debug=True)
    
    
    