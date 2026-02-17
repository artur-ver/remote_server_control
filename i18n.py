from flask import session
from languages import SUPPORTED_LANGS, TRANSLATIONS

def get_lang():
    lang = session.get("lang", None)
    if not lang or lang not in SUPPORTED_LANGS:
        return "ru"
    return lang

def tr(key):
    lang = get_lang()
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS.get("en", {}).get(key, key))

def inject_i18n():
    return {"t": tr, "lang": get_lang(), "langs": SUPPORTED_LANGS}
