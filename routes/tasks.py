import subprocess
from flask import render_template, request, flash, redirect, url_for
from utils import schtasks_list
from i18n import tr

def tasks():
    if request.method == "POST":
        name = request.form.get("name", "")
        action = request.form.get("action", "run")
        
        if name:
            try:
                cmd = []
                msg_success = ""
                
                if action == "run":
                    cmd = ["schtasks", "/Run", "/TN", name]
                    msg_success = tr("task.started")
                elif action == "stop":
                    cmd = ["schtasks", "/End", "/TN", name]
                    msg_success = tr("task.stopped")
                elif action == "enable":
                    cmd = ["schtasks", "/Change", "/TN", name, "/ENABLE"]
                    msg_success = tr("task.enabled")
                elif action == "disable":
                    cmd = ["schtasks", "/Change", "/TN", name, "/DISABLE"]
                    msg_success = tr("task.disabled")
                elif action == "delete":
                    cmd = ["schtasks", "/Delete", "/TN", name, "/F"]
                    msg_success = tr("task.deleted")
                
                if cmd:
                    # Windows schtasks output is often cp866 or utf-8 depending on system
                    res = subprocess.run(cmd, capture_output=True, text=True, encoding="cp866", errors="replace")
                    if res.returncode == 0:
                        flash(msg_success, "success")
                    else:
                        # Sometimes stderr is empty but stdout has error message
                        err_msg = (res.stderr or res.stdout).strip()
                        flash(err_msg, "danger")
            except Exception as e:
                flash(str(e), "danger")
        return redirect(url_for("tasks"))
        
    return render_template("tasks.html", tasks=schtasks_list())
