import os
import sys

# Ensure dependencies are found
site_packages = r"C:\Users\artur\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"
if site_packages not in sys.path:
    sys.path.append(site_packages)

from flask import Flask
from utils import bytes_human
from i18n import inject_i18n

# Import routes
from routes import main, files, terminal, monitor, processes, services, ports, network, disks, system, tasks, logs, power, scripts

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    base_dir = os.environ.get("RSC_BASE_DIR", os.getcwd())
    scripts_dir = os.environ.get("RSC_SCRIPTS_DIR", os.path.join(base_dir, "scripts"))

    app.config["BASE_DIR"] = os.path.abspath(base_dir)
    app.config["SCRIPTS_DIR"] = os.path.abspath(scripts_dir)

    # Context processors
    app.context_processor(inject_i18n)
    
    # Filters
    app.add_template_filter(bytes_human, "bytes_human")

    # Routes
    app.add_url_rule("/", "index", main.index)
    app.add_url_rule("/lang/<lang>", "set_lang", main.set_lang)
    
    app.add_url_rule("/files", "browse", files.browse)
    app.add_url_rule("/upload", "upload", files.upload, methods=["POST"])
    app.add_url_rule("/view", "view_file", files.view_file)
    app.add_url_rule("/edit", "edit_file", files.edit_file, methods=["GET", "POST"])
    app.add_url_rule("/download", "download_file", files.download_file)
    app.add_url_rule("/backup", "backup", files.backup, methods=["GET", "POST"])
    
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
    app.run(host="0.0.0.0", port=port, debug=debug_flag, use_reloader=debug_flag)
