from flask import Blueprint, render_template, redirect, url_for, request, flash
from .db import *
from .decorators import *

sp_pay_bp = Blueprint('sp_pay', __name__, url_prefix='')

@sp_pay_bp.route('sp/pay')
@role_required(['admin', 'admin_viewer'])
def sp():
    db = get_db()
    pays = db.execute("select * from v_pay_info pay where pay != price order by t_d desc, t_t desc").fetchall()
    pays_done = db.execute("select * from v_pay_info pay where pay = price order by t_d desc, t_t desc").fetchall()
    people_ol = db.execute('select ku, naim from sp_ol where in_theater and could_pay order by naim').fetchall()
    people_dr = db.execute("select ku, naim, cy_dr from v_dr_info order by to_date(cy_dr, 'dd.mm.yyyy') desc, naim").fetchall()
    return render_template('sp/pay/sp.html', pays=pays, pays_done=pays_done, people_ol=people_ol, people_dr=people_dr)

@sp_pay_bp.route('/sp/pay/add', methods=['POST'])
@role_required(['admin', 'admin_viewer'])
def add():
    ku_ol, ol_naim = request.form.get('ol').split('|', 1)
    ku_dr, dr_naim = request.form.get('dr').split('|', 1)
    pay = request.form.get('pay')

    try:
        db = get_db()
        db.execute('insert into sp_pay (ku_ol, ku_dr, pay) values (%s, %s, %s)',
                   (ku_ol, ku_dr, pay))
        db.commit()
        flash('Новый долг добавлен', 'success')
    except psycopg.errors.UniqueViolation as e:
        db.rollback()
        if 'uq_pay' in str(e):
            flash(f'Долг для {ol_naim} на день рождения {dr_naim} уже есть', 'danger')
    except psycopg.errors.RaiseException as e:
        db.rollback()
        if 'sp_pay_ol_dr_not_self' in str(e):
            flash('Нельзя добавить долг для человека на его же день рождения', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('sp_pay.sp'))

@sp_pay_bp.route('sp/pay/<int:ku>/edit', methods=['POST'])
@role_required(['admin'])
def edit(ku):
    event_year = request.form.get('event_year')
    price = request.form.get('price')

    try:
        db = get_db()
        db.execute(
            'update sp_dr set event_year = %s, price = %s where ku = %s',
            (event_year, price, ku)
        )
        db.commit()
        flash('Изменено', 'success')
    except psycopg.errors.UniqueViolation as e:
        db.rollback()
        if 'sp_dr_uq' in str(e):
            flash(f'День рождения для этого человека в {event_year} году уже есть', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('sp_dr.dr', ku=ku))

@sp_pay_bp.route('sp/pay/<int:ku>/delete', methods=['POST'])
@role_required(['admin'])
def delete(ku):
    try:
        db = get_db()
        db.execute('delete from sp_dr where ku = %s', (ku,))
        db.commit()
        flash('День рождения успешно удалён', 'success')
        return redirect(url_for('sp_dr.sp'))
    except Exception as e:
        if db: db.rollback()
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('sp_dr.dr', ku=ku))
    finally:
        if db: db.close()