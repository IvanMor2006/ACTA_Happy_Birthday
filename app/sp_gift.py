from flask import Blueprint, render_template, redirect, url_for, request, flash
from .db import *
from .decorators import *

sp_gift_bp = Blueprint('sp_gift', __name__, url_prefix='')

@sp_gift_bp.route('/sp/ol/<int:ku_ol>/gift/add', methods=['POST'])
@login_required
def add(ku_ol):
    ref = request.referrer

    naim = request.form.get('a_gift_naim') or None
    cost = request.form.get('a_gift_cost') or None
    url = request.form.get('a_gift_url')
    status = request.form.get('a_gift_status')

    file = request.files.get('a_gift_img')
    img = None
    if file and file.filename != '':
        img = file.read()

    try:
        db = get_db()
        if status:
            db.execute('insert into sp_gift (naim, cost, img, url, status, ku_ol) values (%s, %s, %s, %s, %s, %s)',
                    (naim, cost, img, url, status, ku_ol))
        else:
            db.execute('insert into sp_gift (naim, cost, img, url, ku_ol) values (%s, %s, %s, %s, %s)',
                    (naim, cost, img, url, ku_ol))
        db.commit()
        flash('Новый подарок добавлен', 'success')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(ref)

@sp_gift_bp.route('/sp/ol/<int:ku_ol>/gift/delete', methods=['POST'])
@login_required
def delete(ku_ol):
    ref = request.referrer
    ku = request.form.get('d_gift_ku')
    try:
        db = get_db()
        db.execute('delete from sp_gift where ku = %s', (ku,))
        db.commit()
        flash('Подарок успешно удалён', 'success')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(ref)