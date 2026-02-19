import psutil
from flask import render_template, request, flash, redirect, url_for
from i18n import tr

def processes():
    procs = []
    for p in psutil.process_iter(attrs=["pid", "name", "username", "cpu_percent", "memory_info"]):
        info = p.info
        mem = info.get("memory_info")
        procs.append(
            {
                "pid": info.get("pid"),
                "name": info.get("name"),
                "user": info.get("username"),
                "cpu": info.get("cpu_percent"),
                "mem": mem.rss if mem else 0,
            }
        )
    procs.sort(key=lambda x: (x["cpu"] or 0), reverse=True)
    return render_template("processes.html", processes=procs[:200])

def processes_kill():
    pid = request.form.get("pid", type=int)
    if not pid:
        flash(tr("proc.pid_not_specified"), "warning")
        return redirect(url_for("processes"))
    try:
        psutil.Process(pid).terminate()
        flash(f"{tr('proc.terminated')} {pid}", "success")
    except psutil.NoSuchProcess:
        flash(tr("proc.not_found"), "warning")
    except psutil.AccessDenied:
        flash(tr("proc.access_denied"), "danger")
    except Exception as e:
        flash(f"{tr('msg.error')}: {e}", "danger")
    return redirect(url_for("processes"))
