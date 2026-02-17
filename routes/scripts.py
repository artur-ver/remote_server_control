import os
import sys
import pathlib
import subprocess
import threading
import time
from datetime import datetime
from flask import current_app, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from utils import safe_join
from i18n import tr

# Global state
# SCRIPT_STATES: script_name -> {
#   'status': 'running' | 'finished' | 'stopped' | 'error',
#   'pid': int,
#   'returncode': int,
#   'stdout': str,
#   'stderr': str,
#   'start_time': str,
#   'end_time': str
# }
SCRIPT_STATES = {}
ACTIVE_PROCESSES = {} # script_name -> Popen object

def monitor_process(script_name, process):
    try:
        stdout, stderr = process.communicate()
        returncode = process.returncode
    except Exception as e:
        stdout = ""
        stderr = str(e)
        returncode = -1

    if script_name in ACTIVE_PROCESSES:
        del ACTIVE_PROCESSES[script_name]
    
    state = SCRIPT_STATES.get(script_name, {})
    state['returncode'] = returncode
    state['stdout'] = stdout or ""
    state['stderr'] = stderr or ""
    state['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if returncode == 0:
        state['status'] = 'finished'
    else:
        state['status'] = 'error'
    
    SCRIPT_STATES[script_name] = state

def scripts():
    scripts_root = current_app.config["SCRIPTS_DIR"]
    os.makedirs(scripts_root, exist_ok=True)
    entries = []
    try:
        for name in os.listdir(scripts_root):
            full = os.path.join(scripts_root, name)
            if os.path.isfile(full) and os.path.splitext(name)[1].lower() in [".py", ".bat", ".sh", ".ps1"]:
                state = SCRIPT_STATES.get(name, {'status': 'stopped'})
                entries.append({
                    "name": name,
                    "status": state.get('status', 'stopped'),
                    "returncode": state.get('returncode'),
                    "start_time": state.get('start_time'),
                    "end_time": state.get('end_time')
                })
    except Exception:
        pass
    
    # Sort: running first, then by name
    entries.sort(key=lambda x: (0 if x['status'] == 'running' else 1, x["name"].lower()))
    return render_template("scripts.html", scripts=entries)

def run_script():
    script_name = request.form.get("script")
    args_line = request.form.get("args", "").strip()
    
    if not script_name:
        flash(tr("msg.script_not_chosen"), "warning")
        return redirect(url_for("scripts"))

    if script_name in ACTIVE_PROCESSES:
        flash(tr("msg.script_running"), "warning")
        return redirect(url_for("scripts"))

    scripts_root = current_app.config["SCRIPTS_DIR"]
    script_path = safe_join(scripts_root, secure_filename(script_name))
    
    if not os.path.exists(script_path):
        flash(tr("msg.script_not_found"), "danger")
        return redirect(url_for("scripts"))

    ext = pathlib.Path(script_path).suffix.lower()
    if ext not in [".py", ".bat", ".sh", ".ps1"]:
        flash(tr("msg.only_py_bat"), "danger")
        return redirect(url_for("scripts"))

    if args_line:
        extra_args = args_line.split()
    else:
        extra_args = []

    cmd = []
    if ext == ".py":
        cmd = [sys.executable, "-u", script_path] + extra_args # -u for unbuffered
    elif ext == ".bat":
        cmd = ["cmd", "/c", script_path] + extra_args
    elif ext == ".ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path] + extra_args
    else:
        # Default fallback
        cmd = [script_path] + extra_args

    try:
        # Start background process
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(script_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False # Better security
        )
        
        ACTIVE_PROCESSES[script_name] = proc
        SCRIPT_STATES[script_name] = {
            'status': 'running',
            'pid': proc.pid,
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stdout': '',
            'stderr': ''
        }
        
        # Start monitoring thread
        thread = threading.Thread(target=monitor_process, args=(script_name, proc))
        thread.daemon = True
        thread.start()
        
        # flash(f"Script {script_name} started (PID: {proc.pid})", "success")
        return redirect(url_for("scripts"))
        
    except Exception as e:
        flash(f"{tr('msg.script_error')}: {e}", "danger")
        return redirect(url_for("scripts"))

def stop_script(name):
    if name in ACTIVE_PROCESSES:
        proc = ACTIVE_PROCESSES[name]
        try:
            proc.terminate()
            # Give it a moment to terminate gracefully
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            
            flash(tr("msg.script_stopped"), "success")
        except Exception as e:
            flash(f"Error stopping script: {e}", "danger")
    
    return redirect(url_for("scripts"))

def upload_script():
    if "file" not in request.files:
        flash(tr("msg.file_not_chosen"), "warning")
        return redirect(url_for("scripts"))
        
    f = request.files["file"]
    if f.filename == "":
        flash(tr("msg.file_not_chosen"), "warning")
        return redirect(url_for("scripts"))
        
    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".py", ".bat", ".sh", ".ps1"]:
        flash(tr("msg.only_py_bat"), "danger")
        return redirect(url_for("scripts"))
        
    scripts_root = current_app.config["SCRIPTS_DIR"]
    os.makedirs(scripts_root, exist_ok=True)
    save_path = os.path.join(scripts_root, filename)
    
    try:
        f.save(save_path)
        flash(tr("msg.script_uploaded"), "success")
    except Exception as e:
        flash(f"{tr('msg.file_not_saved')}: {e}", "danger")
        
    return redirect(url_for("scripts"))

def get_script_output(name):
    state = SCRIPT_STATES.get(name)
    if not state:
        return jsonify({"error": "No state found"}), 404
    
    return jsonify({
        "status": state.get("status"),
        "stdout": state.get("stdout", ""),
        "stderr": state.get("stderr", ""),
        "returncode": state.get("returncode")
    })
