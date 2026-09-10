import dotenv, os, psycopg, pymorphy3, base64

dotenv.load_dotenv()
DB_URL = os.getenv('DB_URL')
_morph_analyzer = None
_naims = {'Куря': 'Кури', 'Амина': 'Амины'}

def get_db():
    return psycopg.connect(DB_URL, row_factory=psycopg.rows.dict_row)

def data_to_img(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return None

def naim_rp(naim):
    global _morph_analyzer, _naims

    if _morph_analyzer is None: _morph_analyzer = pymorphy3.MorphAnalyzer()

    if naim in _naims:
        return _naims[naim]

    try:
        parsed  = _morph_analyzer.parse(naim)[0]
        inflected = parsed.inflect({'gent'})
        if inflected:
            rp = inflected.word.capitalize()
            _naims[naim] = rp
        else:
            rp = naim
    except Exception:
        rp = naim
    return rp