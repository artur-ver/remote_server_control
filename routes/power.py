import os
import subprocess
from flask import render_template, request, flash, redirect, url_for
from i18n import tr

def power():
    allowed = os.environ.get("ALLOW_POWER", "0") == "1"
    msg = None
    if request.method == "POST":
        if not allowed:
            flash(tr("power.forbidden"), "danger")
            return redirect(url_for("power"))
        action = request.form.get("action")
        if action in ["reboot", "shutdown"]:
            try:
                if action == "reboot":
                    subprocess.Popen(["shutdown", "/r", "/t", "5"])
                    msg = tr("power.reboot_init")
                else:
                    subprocess.Popen(["shutdown", "/s", "/t", "5"])
                    msg = tr("power.shutdown_init")
                flash(msg, "warning")
            except Exception as e:
                flash(f"{tr('msg.error')}: {e}", "danger")
    return render_template("power.html", allowed=allowed)
