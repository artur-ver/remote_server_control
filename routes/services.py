import subprocess
from flask import render_template, request, flash, redirect, url_for
from utils import parse_sc_query

def services():
    items = parse_sc_query()
    return render_template("services.html", services=items)

def services_action():
    name = request.form.get("name", "")
    action = request.form.get("action", "")
    if not name or action not in ["start", "stop"]:
        flash("Неверные параметры", "warning")
        return redirect(url_for("services"))
    try:
        res = subprocess.run(["sc", action, name], capture_output=True, text=True, encoding="cp866", errors="replace")
        if res.returncode == 0:
            flash(f"Команда выполнена: {action} {name}", "success")
        else:
            flash(f"Ошибка: {res.stdout or res.stderr}", "danger")
    except Exception as e:
        flash(f"Ошибка: {e}", "danger")
    return redirect(url_for("services"))
