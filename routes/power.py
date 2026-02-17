import os
import subprocess
from flask import render_template, request, flash, redirect, url_for

def power():
    allowed = os.environ.get("ALLOW_POWER", "0") == "1"
    msg = None
    if request.method == "POST":
        if not allowed:
            flash("Действие запрещено (ALLOW_POWER=1 не установлен)", "danger")
            return redirect(url_for("power"))
        action = request.form.get("action")
        if action in ["reboot", "shutdown"]:
            try:
                if action == "reboot":
                    subprocess.Popen(["shutdown", "/r", "/t", "5"])
                    msg = "Перезагрузка инициирована"
                else:
                    subprocess.Popen(["shutdown", "/s", "/t", "5"])
                    msg = "Выключение инициировано"
                flash(msg, "warning")
            except Exception as e:
                flash(f"Ошибка: {e}", "danger")
    return render_template("power.html", allowed=allowed)
