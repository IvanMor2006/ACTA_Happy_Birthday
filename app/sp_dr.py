from flask import Blueprint, render_template, redirect, url_for, request, flash
from .db import *
from .decorators import *

sp_dr_bp = Blueprint('sp_dr', __name__, url_prefix='')

@sp_dr_bp.route('sp/dr')
def sp():
    db = get_db()
    people = db.execute("select * from v_dr_info dr order by to_date(dr.cy_dr, 'DD.MM.YYYY') desc, naim").fetchall()
    people_ol = db.execute('''
        with t as (
        select ol.ku, ol.naim,
                max(dr.event_year) y_dr, to_char(ol.dr, 'mm-dd') md_dr
        from sp_ol ol
        left join sp_dr dr on dr.ku_ol = ol.ku
        group by ol.ku
        )
        select * from t
        order by
            case when md_dr is null then 1 else 0 end
        , case when y_dr is null then 0
                when y_dr < extract(year from current_date) then 1 else 2 end
        , y_dr
        , case when md_dr >= to_char(current_date, 'mm-dd') then 0 else 1 end
        , md_dr
    ''').fetchall()
    return render_template('sp/dr/sp.html', people=people, people_ol=people_ol)

@sp_dr_bp.route('/sp/dr/<int:ku>')
@login_required
def dr(ku):
    db = get_db()
    dr = db.execute('select * from v_dr_info where ku = %s', (ku,)).fetchone()
    if not dr:
        db.close()
        abort(404)
    pays = db.execute('select * from v_pay_info where ku_dr = %s order by pay, ol_naim', (ku,)).fetchall()
    db.close()
    return render_template('sp/dr/dr.html', dr=dr, pays=pays)

@sp_dr_bp.route('/sp/dr/add', methods=['POST'])
@role_required(['admin'])
def add():
    ku_ol, ol_naim = request.form.get('ol').split('|', 1)
    event_year = request.form.get('event_year')
    price = request.form.get('price')

    try:
        db = get_db()
        db.execute('insert into sp_dr (ku_ol, event_year, price) values (%s, %s, %s)',
                   (ku_ol, event_year, price))
        db.commit()
        flash('Новый день рождения добавлен', 'success')
    except psycopg.errors.UniqueViolation as e:
        db.rollback()
        if 'sp_dr_uq' in str(e):
            flash(f'День рождения для {ol_naim} в {event_year} году уже есть', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Ошибка: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('sp_dr.sp'))

@sp_dr_bp.route('sp/dr/<int:ku>/edit', methods=['POST'])
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

@sp_dr_bp.route('sp/dr/<int:ku>/delete', methods=['POST'])
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