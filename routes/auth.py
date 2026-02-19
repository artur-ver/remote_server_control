import os
from flask import render_template, request, redirect, url_for, session, flash
from i18n import tr

FAILED_ATTEMPTS = {}
BLACKLIST_CACHE = None
BLACKLIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blacklist.txt")

def get_client_ip():
    xf = request.headers.get("X-Forwarded-For", "")
    if xf:
        return xf.split(",")[0].strip()
    return request.remote_addr or ""

def load_blacklist():
    global BLACKLIST_CACHE
    if BLACKLIST_CACHE is not None:
        return BLACKLIST_CACHE
    s = set()
    try:
        with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
            for line in f:
                ip = line.strip()
                if ip:
                    s.add(ip)
    except Exception:
        pass
    BLACKLIST_CACHE = s
    return s

def is_blacklisted(ip):
    return ip in load_blacklist()

def blacklist_ip(ip):
    if not ip:
        return
    bl = load_blacklist()
    if ip in bl:
        return
    try:
        with open(BLACKLIST_PATH, "a", encoding="utf-8") as f:
            f.write(ip + "\n")
    except Exception:
        pass
    bl.add(ip)

def login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("index")
    ip = get_client_ip()
    if is_blacklisted(ip):
        return (tr("auth.access_denied"), 403)
    if session.get("auth"):
        return redirect(next_url)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "alfa" and password == "1313":
            session["auth"] = True
            session["user"] = username
            FAILED_ATTEMPTS.pop(ip, None)
            return redirect(next_url)
        cnt = FAILED_ATTEMPTS.get(ip, 0) + 1
        FAILED_ATTEMPTS[ip] = cnt
        if cnt >= 3:
            blacklist_ip(ip)
            return (tr("auth.access_denied"), 403)
        flash(tr("auth.invalid"), "danger")
    return render_template("login.html", hide_nav=True, next_url=next_url)

def logout():
    session.clear()
    return redirect(url_for("login"))
