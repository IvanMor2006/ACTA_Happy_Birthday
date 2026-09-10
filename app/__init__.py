from flask import Flask, render_template
import dotenv, os, pymorphy3

from .user_session import *
from .auth import auth_bp
from .sp_ol import sp_ol_bp
from .sp_dr import sp_dr_bp
from .sp_pay import sp_pay_bp
from .sp_gift import sp_gift_bp
from .db import *
from .decorators import *

dotenv.load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    app.register_blueprint(auth_bp)
    app.register_blueprint(sp_ol_bp)
    app.register_blueprint(sp_dr_bp)
    app.register_blueprint(sp_pay_bp)
    app.register_blueprint(sp_gift_bp)

    @app.context_processor
    def inject_user():
        return dict(
            pending_ku = session_get(PENDING_KU),
            code_sent = session_get(CODE_SENT),

            user_ku = session_get(USER_KU),
            user_name = session_get(USER_NAME, 'Гость'),
            user_role = session_get(USER_ROLE, 'guest'),
        )

    app.jinja_env.filters['naim_rp'] = naim_rp
    app.jinja_env.filters['data_to_img'] = data_to_img

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/sp/card')
    @login_required
    def card():
        return render_template('sp/card.html')

    return app