from flask import render_template, session, redirect, url_for, request
from languages import SUPPORTED_LANGS

def index():
    return render_template("index.html")

def set_lang(lang):
    if lang not in SUPPORTED_LANGS:
        lang = "ru"
    session["lang"] = lang
    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)
    ref = request.headers.get("Referer")
    if ref:
        return redirect(ref)
    return redirect(url_for("index"))
