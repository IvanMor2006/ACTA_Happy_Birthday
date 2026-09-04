import dotenv, os, requests

dotenv.load_dotenv()
TOKEN = os.getenv('TG_BOT_TOKEN')

class TelegramError(Exception):
    pass

def send_telegram_message(user_id, message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    response = requests.post(url, json= {
        'chat_id': user_id,
        'text': message,
        'parse_mode': 'HTML'
    })
    data = response.json()
    if not data['ok']:
        raise TelegramError(data['description'])
    return data