import subprocess
from flask import render_template, request, flash
from utils import schtasks_list
from i18n import tr

def tasks():
    if request.method == "POST":
        name = request.form.get("name", "")
        if name:
            try:
                res = subprocess.run(["schtasks", "/Run", "/TN", name], capture_output=True, text=True, encoding="cp866", errors="replace")
                if res.returncode == 0:
                    flash(tr("task.started"), "success")
                else:
                    flash(res.stdout or res.stderr, "danger")
            except Exception as e:
                flash(str(e), "danger")
    return render_template("tasks.html", tasks=schtasks_list())
