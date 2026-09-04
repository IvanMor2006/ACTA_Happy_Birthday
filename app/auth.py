from flask import Blueprint, render_template, redirect, url_for, request, flash
import bcrypt, secrets

from .bot import *
from .user_session import *
from .db import *

auth_bp = Blueprint('auth', __name__, url_prefix='')

@auth_bp.route('/exit')
def exit():
    session_clear_auth()
    session_clear_user()
    flash('Успешный выход из аккаунта', 'secondary')
    return redirect(url_for('index'))

@auth_bp.route('/login')
def login():
    db = get_db()
    people = db.execute('select * from sp_ol where tg_id is not null order by naim').fetchall()
    db.close()
    return render_template('login.html', people=people)

@auth_bp.route('/login/password', methods=['POST'])
def login_password():
    ku_ol = request.form.get('ku_ol')
    session_set(PENDING_KU, ku_ol)
    session_clear_auth()
    password = request.form.get('password')

    db = get_db()
    user = db.execute('select * from sp_ol where ku = %s and password_hash is not null', (ku_ol,)).fetchone()
    db.close()

    if user:
        if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            session_set_user(user)
            flash('Успешный вход!', 'success')
            return redirect(url_for('sp_ol.ol', ku=ku_ol))
        elif 'forgot' in request.form:
            session_set(PENDING_PASSWORD_HASH, bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
            session_set(CODE_SENT, False)
            return redirect(url_for('auth.login_code'))
        else:
            flash('Неверный пароль!', 'danger')
            return redirect(url_for('auth.login'))
    else:
        session_set(PENDING_PASSWORD_HASH, bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
        session_set(CODE_SENT, False)
        return redirect(url_for('auth.login_code'))

@auth_bp.route('/login/code')
def login_code():
    return render_template('login_code.html', code_sent=session_get(CODE_SENT))

@auth_bp.route('/login/code/send', methods=['POST'])
def login_code_send():
    ku_ol = session_get(PENDING_KU)
    db = get_db()
    tg_id = db.execute('select tg_id from sp_ol where ku = %s', (ku_ol,)).fetchone()['tg_id']
    db.close()
    if not tg_id:
        session_clear_auth()
        session_pop(PENDING_KU)
        flash('Пользователь не найден или не привязан к Telegram!', 'danger')
        return redirect(url_for('auth.login'))
    code = secrets.randbelow(900000) + 100000
    try:
        send_telegram_message(tg_id, f'Ваш код подтверждения: {code}')
        session_set(PENDING_CODE_HASH, bcrypt.hashpw(str(code).encode(), bcrypt.gensalt()).decode())
        session_set(CODE_SENT, True)
        flash('Код подтверждения отправлен в Telegram!', 'success')
    except TelegramError:
        session_set(CODE_SENT, False)
        flash('Не удалось отправить код подтверждения. Пожалуйста, убедитесь, что вы начали диалог с ботом в Telegram.', 'danger')
    except requests.exceptions.RequestException:
        session_set(CODE_SENT, False)
        flash('Ошибка соединения с Telegram. Попробуйте позже.', 'danger')
    except Exception as e:
        session_set(CODE_SENT, False)
        flash(f'Произошла ошибка: {e}', 'danger')
    return redirect(url_for('auth.login_code'))

@auth_bp.route('/login/code/verify', methods=['POST'])
def login_code_verify():
    code = request.form.get('code')
    true_code = session_get(PENDING_CODE_HASH)

    if true_code and bcrypt.checkpw(code.encode(), true_code.encode()):
        ku_ol = session_get(PENDING_KU)
        db = get_db()
        user = db.execute('select * from sp_ol where ku = %s', (ku_ol,)).fetchone()
        if user:
            db.execute('update sp_ol set password_hash = %s where ku = %s', (session_get(PENDING_PASSWORD_HASH), ku_ol))
            db.commit()
            db.close()
            session_clear_auth()
            session_set_user(user)
            flash('Успешная регистрация!', 'success')
            return redirect(url_for('sp_ol.ol', ku=ku_ol))
        else:
            db.close()
            session_clear_auth()
            session_pop(PENDING_KU)
            flash('Пользователь не найден!', 'danger')
            return redirect(url_for('auth.login'))
    else:
        session_pop(PENDING_CODE_HASH)
        session_set(CODE_SENT, False)
        flash('Неверный код подтверждения!', 'danger')
        return redirect(url_for('auth.login_code'))