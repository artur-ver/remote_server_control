import os
import sys

# Ensure site-packages is in path (Windows-specific fix for Store Python)
if os.name == 'nt':
    site_packages = r"C:\Users\artur\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"
    if os.path.exists(site_packages) and site_packages not in sys.path:
        sys.path.append(site_packages)

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from utils import bytes_human, get_local_ip, get_all_ips
from i18n import inject_i18n, tr

# Import routes
from routes import main, files, terminal, monitor, processes, services, ports, network, disks, system, tasks, logs, power, scripts
from routes import auth

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    base_dir = os.environ.get("RSC_BASE_DIR", os.getcwd())
    scripts_dir = os.environ.get("RSC_SCRIPTS_DIR", os.path.join(base_dir, "scripts"))

    app.config["BASE_DIR"] = os.path.abspath(base_dir)
    app.config["SCRIPTS_DIR"] = os.path.abspath(scripts_dir)
    app.config["LOCAL_IP"] = get_local_ip()

    # Context processors
    app.context_processor(inject_i18n)
    
    @app.context_processor
    def inject_network_info():
        protocol = "https" if "ssl" in sys.argv else "http"
        return dict(local_ip=app.config["LOCAL_IP"], port=int(os.environ.get("PORT", "5000")), protocol=protocol)
    
    # Filters
    app.add_template_filter(bytes_human, "bytes_human")

    # Routes
    app.add_url_rule("/", "index", main.index)
    app.add_url_rule("/lang/<lang>", "set_lang", main.set_lang)
    app.add_url_rule("/login", "login", auth.login, methods=["GET", "POST"])
    app.add_url_rule("/logout", "logout", auth.logout)
    
    @app.before_request
    def require_login():
        from flask import request, redirect, url_for, session
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr
        if auth.is_blacklisted(ip or ""):
            return (tr("auth.access_denied"), 403)
        allowed = set(["static", "login", "set_lang"])
        if request.endpoint and request.endpoint in allowed:
            return None
        if not session.get("auth"):
            next_url = request.full_path if request.query_string else request.path
            return redirect(url_for("login", next=next_url))
        return None
    
    app.add_url_rule("/files", "browse", files.browse)
    app.add_url_rule("/upload", "upload", files.upload, methods=["POST"])
    app.add_url_rule("/view", "view_file", files.view_file)
    app.add_url_rule("/edit", "edit_file", files.edit_file, methods=["GET", "POST"])
    app.add_url_rule("/download", "download_file", files.download_file)
    app.add_url_rule("/backup", "backup", files.backup, methods=["GET", "POST"])
    
    # Trash routes
    app.add_url_rule("/files/trash", "trash_list", files.trash_list)
    app.add_url_rule("/files/trash/add", "trash_add", files.trash_add)
    app.add_url_rule("/files/trash/restore", "trash_restore", files.trash_restore, methods=["POST"])
    app.add_url_rule("/files/trash/delete", "trash_delete", files.trash_delete, methods=["POST"])
    app.add_url_rule("/files/trash/empty", "trash_empty", files.trash_empty, methods=["POST"])
    
    app.add_url_rule("/terminal", "terminal", terminal.terminal, methods=["GET"])
    app.add_url_rule("/terminal/exec", "terminal_exec", terminal.terminal_exec, methods=["POST"])
    app.add_url_rule("/terminal/clear", "terminal_clear", terminal.terminal_clear, methods=["POST"])
    app.add_url_rule("/terminal/reset", "terminal_reset", terminal.terminal_reset, methods=["POST"])
    
    app.add_url_rule("/monitor", "monitor", monitor.monitor)
    app.add_url_rule("/metrics", "metrics", monitor.metrics)
    
    app.add_url_rule("/processes", "processes", processes.processes)
    app.add_url_rule("/processes/kill", "processes_kill", processes.processes_kill, methods=["POST"])
    
    app.add_url_rule("/services", "services", services.services)
    app.add_url_rule("/services/action", "services_action", services.services_action, methods=["POST"])
    
    app.add_url_rule("/ports", "ports", ports.ports)
    
    app.add_url_rule("/network", "network", network.network, methods=["GET", "POST"])
    
    app.add_url_rule("/disks", "disks", disks.disks)
    
    app.add_url_rule("/system", "system_info", system.system_info)
    
    app.add_url_rule("/tasks", "tasks", tasks.tasks, methods=["GET", "POST"])
    
    app.add_url_rule("/logs", "logs", logs.logs, methods=["GET", "POST"])
    
    app.add_url_rule("/power", "power", power.power, methods=["GET", "POST"])
    
    app.add_url_rule("/scripts", "scripts", scripts.scripts)
    app.add_url_rule("/run", "run_script", scripts.run_script, methods=["POST"])
    app.add_url_rule("/scripts/upload", "upload_script", scripts.upload_script, methods=["POST"])
    app.add_url_rule("/scripts/stop/<name>", "stop_script", scripts.stop_script, methods=["POST"])
    app.add_url_rule("/scripts/output/<name>", "get_script_output", scripts.get_script_output)

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", "5000"))
    debug_flag = os.environ.get("FLASK_DEBUG", "1") == "1"
    
    local_ip = app.config["LOCAL_IP"]
    all_ips = get_all_ips()
    
    # Check if user wants to run with adhoc SSL (simple argument check)
    if "ssl" in sys.argv:
        print(f"\n{'='*50}")
        print(f" RSC Server Starting (HTTPS Mode)...")
        print(" * Note: You will see a security warning in the browser because the certificate is self-signed.")
        print(f" * Secure Local Access:   https://127.0.0.1:{port}")
        if all_ips:
            for ip in all_ips:
                print(f" * Secure Network Access: https://{ip}:{port}")
        else:
            print(f" * Secure Network Access: https://{local_ip}:{port}")
        print(f"{'='*50}\n")
        app.run(host="0.0.0.0", port=port, debug=debug_flag, use_reloader=debug_flag, ssl_context='adhoc')
    else:
        print(f"\n{'='*50}")
        print(f" RSC Server Starting (HTTP Mode)...")
        print(f" Local Access:   http://127.0.0.1:{port}")
        if all_ips:
            for ip in all_ips:
                 print(f" Network Access: http://{ip}:{port}")
        else:
            print(f" Network Access: http://{local_ip}:{port}")
        print(f"{'='*50}\n")
        app.run(host="0.0.0.0", port=port, debug=debug_flag, use_reloader=debug_flag)
