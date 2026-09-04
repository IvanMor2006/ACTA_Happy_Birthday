from flask import session

PENDING_KU = 'pending_ku'
PENDING_PASSWORD_HASH = 'pending_password_hash'
PENDING_CODE_HASH = 'pending_code_hash'
CODE_SENT = 'code_sent'

USER_KU = 'user_ku'
USER_NAME = 'user_name'
USER_ROLE = 'user_role'

def session_get(name, default=None):
    return session.get(name, default)
def session_pop(name, default=None):
    return session.pop(name, default)
def session_set(name, value):
    session[name] = value

def session_clear_auth():
    session_pop(PENDING_PASSWORD_HASH)
    session_pop(PENDING_CODE_HASH)
    session_pop(CODE_SENT)

def session_clear_user():
    session_pop(USER_KU)
    session_set(USER_NAME, 'Гость')
    session_set(USER_ROLE, 'guest')
def session_set_user(user):
    session_set(USER_KU, user['ku'])
    session_set(USER_NAME, user['naim'])
    session_set(USER_ROLE, user['role'])