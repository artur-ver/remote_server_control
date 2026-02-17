import subprocess
import os
import platform
from flask import current_app, request, flash, redirect, url_for, render_template, session, jsonify
from utils import safe_join
from i18n import tr

def get_default_shell():
    if platform.system().lower() == "windows":
        return "powershell"
    return "/bin/bash"

def terminal():
    # Session state for CWD
    if "term_cwd" not in session:
        session["term_cwd"] = current_app.config["BASE_DIR"]
    
    # Session state for full output history (list of {cmd, output, cwd, timestamp})
    if "term_output_history" not in session:
        session["term_output_history"] = []
        
    hist = session.get("cmd_history", [])
    
    hide_nav = request.args.get('embedded') == 'true'

    return render_template(
        "terminal.html", 
        last_cmd=None, 
        output_history=session["term_output_history"],
        cmd_history=hist, 
        current_cwd=session["term_cwd"],
        default_shell=get_default_shell(),
        is_windows=(platform.system().lower() == "windows"),
        hide_nav=hide_nav
    )

def terminal_exec():
    cmdline = request.form.get("cmd", "").strip()
    shell = request.form.get("shell", get_default_shell())
    
    # Use session CWD by default, or override if provided (though UI should sync)
    workdir = session.get("term_cwd", current_app.config["BASE_DIR"])
    
    if not cmdline:
        return redirect(url_for("terminal"))

    # Handle 'cd' manually for persistence
    if cmdline.startswith("cd ") or cmdline == "cd":
        try:
            target = cmdline[3:].strip()
            if not target:
                 # cd without args -> home or base
                 new_cwd = current_app.config["BASE_DIR"]
            else:
                 new_cwd = os.path.abspath(os.path.join(workdir, target))
            
            if os.path.isdir(new_cwd):
                session["term_cwd"] = new_cwd
                output = ""
                returncode = 0
            else:
                output = f"cd: {target}: No such file or directory"
                returncode = 1
        except Exception as e:
            output = str(e)
            returncode = 1
    else:
        # Run actual command
        try:
            if platform.system().lower() == "windows":
                if shell == "powershell":
                    command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmdline]
                else:
                    command = ["cmd", "/c", cmdline]
            else:
                # Linux/Unix
                command = [shell, "-c", cmdline]

            proc = subprocess.run(
                command,
                cwd=workdir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                shell=False,
            )
            output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            returncode = proc.returncode
        except subprocess.TimeoutExpired as e:
            output = f"Timeout: {e}"
            returncode = -1
        except Exception as e:
            output = f"Execution error: {e}"
            returncode = -1

    # Update history
    cmd_hist = session.get("cmd_history", [])
    if cmdline not in cmd_hist:
        cmd_hist = (cmd_hist + [cmdline])[-20:]
    session["cmd_history"] = cmd_hist
    
    # Append to output history
    out_hist = session.get("term_output_history", [])
    out_hist.append({
        "cmd": cmdline,
        "output": output,
        "cwd": workdir,
        "code": returncode
    })
    # Keep last 50 entries to avoid session bloat
    session["term_output_history"] = out_hist[-50:]
    
    # Return JSON if requested
    if request.args.get('ajax') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'cmd': cmdline,
            'output': output,
            'cwd': workdir if 'new_cwd' not in locals() else new_cwd,
            'code': returncode
        })

    return redirect(url_for("terminal"))

def terminal_clear():
    session["term_output_history"] = []
    # Don't clear cmd_history (up arrow), just the screen
    if request.args.get('ajax') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'cleared'})
    return redirect(url_for("terminal"))

def terminal_reset():
    session["term_cwd"] = current_app.config["BASE_DIR"]
    session["term_output_history"] = []
    session["cmd_history"] = []
    if request.args.get('ajax') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'reset', 'cwd': session["term_cwd"]})
    flash(tr("msg.history_cleared"), "success")
    return redirect(url_for("terminal"))
