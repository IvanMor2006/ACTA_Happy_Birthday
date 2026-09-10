from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from datetime import datetime

from .db import *
from .decorators import *
from .user_session import *

sp_ol_bp = Blueprint('sp_ol', __name__, url_prefix='')

@sp_ol_bp.route('/sp/ol')
def sp():
    db = get_db()
    people = db.execute('''
        select *
        from v_ol_info
        where in_theater
        order by to_char(dr, 'mmdd'), naim
    ''').fetchall()
    people_arc = db.execute('''
        select *
        from v_ol_info
        where not in_theater and naim not like '%ADMIN%'
        order by to_char(dr, 'mmdd'), naim
    ''').fetchall()
    roles = db.execute('select * from v_roles').fetchall()
    total_debt = db.execute('select * from f_get_debt()').fetchone()['f_get_debt']
    db.close()
    return render_template('sp/ol/sp.html', people=people, people_arc=people_arc, roles=roles, total_debt=total_debt)

@sp_ol_bp.route('/sp/ol/<int:ku>')
@login_required
def ol(ku):
    db = get_db()
    roles = db.execute('select * from v_roles').fetchall()
    person = db.execute('select * from v_ol_info where ku = %s', (ku,)).fetchone()
    if not person:
        db.close()
        abort(404)
    people_ol = db.execute('select ku, naim from sp_ol where in_theater and could_pay order by naim').fetchall()
    people_dr = db.execute("select ku, naim, cy_dr from v_dr_info order by to_date(cy_dr, 'dd.mm.yyyy') desc, naim").fetchall()
    pays = db.execute("select * from v_pay_info where ku_ol = %s order by to_date(cy_dr, 'DD.MM.YYYY') desc", (ku,)).fetchall()

    gift_statuses = db.execute('select * from v_gift_status').fetchall()
    gifts = db.execute('select * from sp_gift where ku_ol = %s order by naim', (ku,)).fetchall()

    db.close()
    return render_template(
        'sp/ol/ol.html',
        person=person, roles=roles,
        people_ol=people_ol, people_dr=people_dr, pays=pays,
        gift_statuses=gift_statuses, gifts=gifts
    )

@sp_ol_bp.route('/sp/ol/add', methods=['POST'])
@role_required(['admin'])
def add():
    naim = request.form.get('ae_ol_naim')
    dr = request.form.get('ae_ol_dr') or None
    tg_id = request.form.get('ae_ol_tg_id') or None
    could_pay = True if request.form.get('ae_ol_could_pay') else False
    in_theater = True if request.form.get('ae_ol_in_theater') else False
    role = request.form.get('ae_ol_role')

    try:
        db = get_db()
        db.execute('insert into sp_ol (naim, dr, tg_id, could_pay, in_theater, role) values (%s, %s, %s, %s, %s, %s)',
                (naim, dr, tg_id, could_pay, in_theater, role))
        db.commit()
        flash('Новый человек добавлен', 'success')
    except psycopg.errors.UniqueViolation as e:
        db.rollback()
        if 'sp_ol_naim_key' in str(e):
            flash('Человек с таким именем уже есть', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('sp_ol.sp'))

@sp_ol_bp.route('/sp/ol/<int:ku>/edit', methods=['POST'])
@role_required(['admin'])
def edit(ku):
    naim = request.form.get('ae_ol_naim') or None
    dr = request.form.get('ae_ol_dr') or None
    tg_id = request.form.get('ae_ol_tg_id') or None
    could_pay = True if request.form.get('ae_ol_could_pay') else False
    in_theater = True if request.form.get('ae_ol_in_theater') else False
    role = request.form.get('ae_ol_role')
    try:
        db = get_db()
        db.execute(
            'update sp_ol set naim = %s, dr = %s, tg_id = %s, could_pay = %s, in_theater = %s, role = %s where ku = %s',
            (naim, dr, tg_id, could_pay, in_theater, role, ku)
        )
        db.commit()
        if ku == session_get(USER_KU):
            session_set(USER_NAME, naim)
            session_set(USER_ROLE, role)
        flash('Изменено', 'success')
    except psycopg.errors.UniqueViolation as e:
        if db: db.rollback()
        if 'sp_ol_naim_key' in str(e):
            flash('Человек с таким именем уже есть', 'danger')
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        if db: db.close()
    return redirect(url_for('sp_ol.ol', ku=ku))

@sp_ol_bp.route('/sp/ol/<int:ku>/delete', methods=['POST'])
@role_required(['admin'])
def delete(ku):
    try:
        db = get_db()
        db.execute('delete from sp_ol where ku = %s', (ku,))
        db.commit()
        if ku == session_get(USER_KU):
            session_clear_user()
        flash('Человек успешно удалён', 'success')
        return redirect(url_for('sp_ol.sp'))
    except psycopg.errors.IntegrityError as e:
        if db: db.rollback()
        if 'sp_pay_ku_ol_fkey' in str(e):
            flash(f'У человека есть долги', 'danger')
        elif 'sp_dr_ku_ol_fkey' in str(e):
            flash(f'У человека есть дни рождения', 'danger')
        else:
            flash('Ошибка целостности', 'danger')
        return redirect(url_for('sp_ol.ol', ku=ku))
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('sp_ol.ol', ku=ku))
    finally:
        if db: db.close()

@sp_ol_bp.route('/sp/ol/<int:ku>/add_money', methods=['POST'])
@role_required(['admin'])
def update_pay(ku):
    if session_get(USER_KU) != ku and session_get(USER_ROLE) != 'admin':
        abort(403)

    db = get_db()
    db.execute(
        'call p_add_to_balance(cast(%s as bigint), cast(%s as numeric), cast(%s as boolean))',
        (ku, float(request.form.get('am_ol_sum')), 'am_ol_auto_debt' in request.form)
    )
    db.commit()
    db.close()
    return redirect(url_for('sp_ol.ol', ku=ku))