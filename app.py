import os
import sys
import mimetypes
import pathlib
import subprocess
import time
import psutil
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, flash, jsonify, session, request as flask_request
from werkzeug.utils import secure_filename


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    base_dir = os.environ.get("RSC_BASE_DIR", os.getcwd())
    scripts_dir = os.environ.get("RSC_SCRIPTS_DIR", os.path.join(base_dir, "scripts"))

    app.config["BASE_DIR"] = os.path.abspath(base_dir)
    app.config["SCRIPTS_DIR"] = os.path.abspath(scripts_dir)

    SUPPORTED_LANGS = ["en", "ru", "cs"]
    TRANSLATIONS = {
        "en": {
            "nav.home": "Home",
            "nav.files": "Files",
            "nav.terminal": "Terminal",
            "nav.scripts": "Scripts",
            "nav.monitor": "Monitoring",
            "breadcrumb.root": "Root",
            "files.title": "File Manager",
            "files.upload.label": "Upload file",
            "files.upload.button": "Upload",
            "table.name": "Name",
            "table.type": "Type",
            "table.size": "Size",
            "table.actions": "Actions",
            "type.dir": "Directory",
            "type.file": "File",
            "action.open": "Open",
            "action.view": "View",
            "action.download": "Download",
            "action.edit": "Edit",
            "view.download": "Download",
            "view.back": "Back to folder",
            "view.not_text": "This file is not a text file. You can download it.",
            "scripts.title": "Scripts",
            "scripts.dir": "Scripts directory",
            "scripts.none": "No scripts. Add .py or .bat to scripts folder.",
            "scripts.select": "Script",
            "scripts.args": "Arguments (space-separated)",
            "scripts.run": "Run",
            "scripts.result": "Run result",
            "scripts.code": "Return code",
            "edit.title": "Editing",
            "edit.view": "View",
            "edit.save": "Save",
            "edit.cancel": "Cancel",
            "term.title": "Terminal",
            "term.command": "Command",
            "term.shell": "Shell",
            "term.cwd": "Working folder (relative to BASE_DIR)",
            "term.execute": "Execute",
            "term.quick.clear": "Clear history",
            "term.return_code": "Return code",
            "monitor.title": "Monitoring",
            "monitor.cpu": "CPU",
            "monitor.mem": "Memory",
            "monitor.net": "Network (Kbit/s)",
            "monitor.disk": "Disk (Kbit/s)",
            "monitor.gpu": "GPU",
            "ui.copy": "Copy",
            "ui.wrap": "Wrap",
            "term.history": "History",
            "msg.no_access": "No access to directory",
            "msg.file_uploaded": "File uploaded",
            "msg.file_not_saved": "Failed to save file",
            "msg.file_not_chosen": "File not chosen",
            "msg.not_found": "Not found",
            "msg.script_not_chosen": "Script name not selected",
            "msg.script_not_found": "Script not found",
            "msg.only_py_bat": "Only .py and .bat allowed",
            "msg.script_error": "Run error",
            "msg.timeout": "Command timeout",
            "msg.exec_error": "Execution error",
            "msg.file_saved": "File saved",
            "msg.edit_binary_forbidden": "Editing binary files is forbidden",
            "msg.edit_not_text": "This file cannot be edited as text",
            "msg.cmd_not_specified": "Command not specified",
            "msg.history_cleared": "History cleared",
        },
        "ru": {
            "nav.home": "Главная",
            "nav.files": "Файлы",
            "nav.terminal": "Терминал",
            "nav.scripts": "Скрипты",
            "nav.monitor": "Мониторинг",
            "breadcrumb.root": "Корень",
            "files.title": "Файловый менеджер",
            "files.upload.label": "Загрузка файла",
            "files.upload.button": "Загрузить",
            "table.name": "Имя",
            "table.type": "Тип",
            "table.size": "Размер",
            "table.actions": "Действия",
            "type.dir": "Каталог",
            "type.file": "Файл",
            "action.open": "Открыть",
            "action.view": "Просмотр",
            "action.download": "Скачать",
            "action.edit": "Редактировать",
            "view.download": "Скачать",
            "view.back": "К каталогу",
            "view.not_text": "Данный файл не текстовый. Вы можете его скачать.",
            "scripts.title": "Скрипты",
            "scripts.dir": "Каталог со скриптами",
            "scripts.none": "Скриптов нет. Добавьте .py или .bat в каталог scripts.",
            "scripts.select": "Скрипт",
            "scripts.args": "Аргументы (через пробел)",
            "scripts.run": "Запустить",
            "scripts.result": "Результат запуска",
            "scripts.code": "Код возврата",
            "edit.title": "Редактирование",
            "edit.view": "Просмотр",
            "edit.save": "Сохранить",
            "edit.cancel": "Отмена",
            "term.title": "Терминал",
            "term.command": "Команда",
            "term.shell": "Shell",
            "term.cwd": "Рабочая папка (относительно BASE_DIR)",
            "term.execute": "Выполнить",
            "term.quick.clear": "Очистить историю",
            "term.return_code": "Код возврата",
            "monitor.title": "Мониторинг",
            "monitor.cpu": "CPU",
            "monitor.mem": "Память",
            "monitor.net": "Сеть (Кбит/с)",
            "monitor.disk": "Диск (Кбит/с)",
            "monitor.gpu": "GPU",
            "ui.copy": "Копировать",
            "ui.wrap": "Перенос",
            "term.history": "История",
            "msg.no_access": "Нет доступа к каталогу",
            "msg.file_uploaded": "Файл загружен",
            "msg.file_not_saved": "Не удалось сохранить файл",
            "msg.file_not_chosen": "Файл не выбран",
            "msg.not_found": "Не найдено",
            "msg.script_not_chosen": "Не выбрано имя скрипта",
            "msg.script_not_found": "Скрипт не найден",
            "msg.only_py_bat": "Разрешены только .py и .bat",
            "msg.script_error": "Ошибка запуска",
            "msg.timeout": "Команда превысила лимит времени",
            "msg.exec_error": "Ошибка выполнения команды",
            "msg.file_saved": "Файл сохранён",
            "msg.edit_binary_forbidden": "Редактирование бинарных файлов запрещено",
            "msg.edit_not_text": "Этот файл нельзя редактировать как текст",
            "msg.cmd_not_specified": "Команда не указана",
            "msg.history_cleared": "История очищена",
        },
        "cs": {
            "nav.home": "Domů",
            "nav.files": "Soubory",
            "nav.terminal": "Terminál",
            "nav.scripts": "Skripty",
            "nav.monitor": "Monitoring",
            "breadcrumb.root": "Kořen",
            "files.title": "Správce souborů",
            "files.upload.label": "Nahrát soubor",
            "files.upload.button": "Nahrát",
            "table.name": "Název",
            "table.type": "Typ",
            "table.size": "Velikost",
            "table.actions": "Akce",
            "type.dir": "Adresář",
            "type.file": "Soubor",
            "action.open": "Otevřít",
            "action.view": "Zobrazit",
            "action.download": "Stáhnout",
            "action.edit": "Upravit",
            "view.download": "Stáhnout",
            "view.back": "Zpět do složky",
            "view.not_text": "Tento soubor není textový. Můžete si ho stáhnout.",
            "scripts.title": "Skripty",
            "scripts.dir": "Složka se skripty",
            "scripts.none": "Žádné skripty. Přidejte .py nebo .bat do složky scripts.",
            "scripts.select": "Skript",
            "scripts.args": "Argumenty (oddělené mezerou)",
            "scripts.run": "Spustit",
            "scripts.result": "Výsledek běhu",
            "scripts.code": "Návratový kód",
            "edit.title": "Úpravy",
            "edit.view": "Zobrazit",
            "edit.save": "Uložit",
            "edit.cancel": "Zrušit",
            "term.title": "Terminál",
            "term.command": "Příkaz",
            "term.shell": "Shell",
            "term.cwd": "Pracovní složka (vůči BASE_DIR)",
            "term.execute": "Spustit",
            "term.quick.clear": "Vymazat historii",
            "term.return_code": "Návratový kód",
            "monitor.title": "Monitoring",
            "monitor.cpu": "CPU",
            "monitor.mem": "Paměť",
            "monitor.net": "Síť (Kbit/s)",
            "monitor.disk": "Disk (Kbit/s)",
            "monitor.gpu": "GPU",
            "ui.copy": "Kopírovat",
            "ui.wrap": "Zalamovat",
            "term.history": "Historie",
            "msg.no_access": "Přístup do adresáře odepřen",
            "msg.file_uploaded": "Soubor nahrán",
            "msg.file_not_saved": "Soubor se nepodařilo uložit",
            "msg.file_not_chosen": "Soubor není vybrán",
            "msg.not_found": "Nenalezeno",
            "msg.script_not_chosen": "Není vybrán název skriptu",
            "msg.script_not_found": "Skript nenalezen",
            "msg.only_py_bat": "Povoleny pouze .py a .bat",
            "msg.script_error": "Chyba spuštění",
            "msg.timeout": "Časový limit příkazu",
            "msg.exec_error": "Chyba provedení příkazu",
            "msg.file_saved": "Soubor uložen",
            "msg.edit_binary_forbidden": "Úprava binárních souborů je zakázána",
            "msg.edit_not_text": "Tento soubor nelze upravovat jako text",
            "msg.cmd_not_specified": "Příkaz není uveden",
            "msg.history_cleared": "Historie vymazána",
        },
    }

    def get_lang():
        lang = session.get("lang", None)
        if not lang or lang not in SUPPORTED_LANGS:
            return "ru"
        return lang

    def tr(key):
        lang = get_lang()
        return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS.get("en", {}).get(key, key))

    @app.context_processor
    def inject_i18n():
        return {"t": tr, "lang": get_lang(), "langs": SUPPORTED_LANGS}

    def safe_join(base, *paths):
        candidate = os.path.abspath(os.path.join(base, *paths))
        base_abs = os.path.abspath(base)
        if os.path.commonpath([candidate, base_abs]) != base_abs:
            abort(403)
        return candidate

    def is_text_file(path, read_bytes=1024):
        try:
            with open(path, "rb") as f:
                chunk = f.read(read_bytes)
            if b"\x00" in chunk:
                return False
            return True
        except Exception:
            return False
    def bytes_human(value):
        try:
            v = float(value)
        except Exception:
            return value
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while v >= 1024 and i < len(units) - 1:
            v /= 1024.0
            i += 1
        if i == 0:
            return f"{int(v)} {units[i]}"
        return f"{v:.1f} {units[i]}"
    app.add_template_filter(bytes_human, "bytes_human")

    def get_gpu_info():
        gpus = []
        # Try NVML (NVIDIA)
        try:
            import pynvml
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(h)
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                name = pynvml.nvmlDeviceGetName(h).decode("utf-8", errors="ignore")
                gpus.append(
                    {
                        "index": i,
                        "name": name,
                        "util_percent": int(getattr(util, "gpu", 0)),
                        "mem_total": int(getattr(mem, "total", 0)),
                        "mem_used": int(getattr(mem, "used", 0)),
                    }
                )
            pynvml.nvmlShutdown()
            return gpus
        except Exception:
            pass
        # Fallback to nvidia-smi if available
        try:
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.total,memory.used", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=3,
            )
            if proc.returncode == 0 and proc.stdout:
                for idx, line in enumerate(proc.stdout.strip().splitlines()):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        try:
                            name, util, mem_total, mem_used = parts[:4]
                            gpus.append(
                                {
                                    "index": idx,
                                    "name": name,
                                    "util_percent": int(float(util)),
                                    "mem_total": int(float(mem_total) * 1024 * 1024),  # MB -> bytes
                                    "mem_used": int(float(mem_used) * 1024 * 1024),
                                }
                            )
                        except Exception:
                            continue
        except Exception:
            pass
        return gpus

    @app.route("/")
    def index():
        return render_template("index.html")
    @app.route("/files")
    def browse():
        rel_path = request.args.get("path", "")
        rel_path = request.args.get("path", "")
        current_path = safe_join(app.config["BASE_DIR"], rel_path)
        if not os.path.exists(current_path):
            abort(404)

        if os.path.isdir(current_path):
            items = []
            try:
                for name in os.listdir(current_path):
                    full = os.path.join(current_path, name)
                    items.append(
                        {
                            "name": name,
                            "is_dir": os.path.isdir(full),
                            "size": os.path.getsize(full) if os.path.isfile(full) else None,
                            "rel_path": os.path.relpath(full, app.config["BASE_DIR"]),
                            "ext": os.path.splitext(name)[1].lower() if os.path.isfile(full) else "",
                        }
                    )
            except PermissionError:
                flash(tr("msg.no_access"), "warning")
                items = []

            parent_rel = None
            rel_norm = os.path.relpath(current_path, app.config["BASE_DIR"])
            if rel_norm != ".":
                parent_rel = os.path.relpath(os.path.dirname(current_path), app.config["BASE_DIR"])
            return render_template(
                "files.html",
                items=sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower())),
                current_rel="" if rel_norm == "." else rel_norm,
                parent_rel=parent_rel if parent_rel != "." else "",
            )
        else:
            return redirect(url_for("view_file", path=rel_path))

    @app.route("/upload", methods=["POST"])
    def upload():
        rel_path = request.form.get("path", "")
        current_path = safe_join(app.config["BASE_DIR"], rel_path)
        if not os.path.isdir(current_path):
            abort(400)
        f = request.files.get("file")
        if not f or f.filename == "":
            flash(tr("msg.file_not_chosen"), "warning")
            return redirect(url_for("browse", path=rel_path))
        filename = secure_filename(f.filename)
        dest = safe_join(current_path, filename)
        try:
            f.save(dest)
            flash(tr("msg.file_uploaded"), "success")
        except Exception:
            flash(tr("msg.file_not_saved"), "danger")
        return redirect(url_for("browse", path=rel_path))

    @app.route("/view")
    def view_file():
        rel_path = request.args.get("path", "")
        file_path = safe_join(app.config["BASE_DIR"], rel_path)
        if not os.path.isfile(file_path):
            abort(404)
        text = None
        if is_text_file(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except Exception:
                text = None
        return render_template(
            "view.html",
            rel_path=os.path.relpath(file_path, app.config["BASE_DIR"]),
            is_text=text is not None,
            text_content=text,
        )

    @app.route("/edit", methods=["GET", "POST"])
    def edit_file():
        rel_path = request.args.get("path") if request.method == "GET" else request.form.get("path")
        if not rel_path:
            abort(400)
        file_path = safe_join(app.config["BASE_DIR"], rel_path)
        if not os.path.isfile(file_path):
            abort(404)
        if request.method == "POST":
            if not is_text_file(file_path):
                flash(tr("msg.edit_binary_forbidden"), "danger")
                return redirect(url_for("view_file", path=rel_path))
            content = request.form.get("content", "")
            try:
                with open(file_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(content)
                flash(tr("msg.file_saved"), "success")
                return redirect(url_for("view_file", path=rel_path))
            except Exception:
                flash(tr("msg.file_not_saved"), "danger")
                return redirect(url_for("edit_file", path=rel_path))
        else:
            if not is_text_file(file_path):
                flash(tr("msg.edit_not_text"), "warning")
                return redirect(url_for("view_file", path=rel_path))
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except Exception:
                text = ""
            return render_template("edit.html", rel_path=os.path.relpath(file_path, app.config["BASE_DIR"]), text_content=text)

    @app.route("/download")
    def download_file():
        rel_path = request.args.get("path", "")
        file_path = safe_join(app.config["BASE_DIR"], rel_path)
        if not os.path.isfile(file_path):
            abort(404)
        mime, _ = mimetypes.guess_type(file_path)
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path), mimetype=mime)

    @app.route("/terminal", methods=["GET"])
    def terminal():
        hist = session.get("cmd_history", [])
        return render_template("terminal.html", last_cmd=None, output=None, code=None, history=hist, base_dir=app.config["BASE_DIR"])

    @app.route("/terminal/exec", methods=["POST"])
    def terminal_exec():
        cmdline = request.form.get("cmd", "").strip()
        shell = request.form.get("shell", "cmd")
        rel_cwd = request.form.get("cwd", "").strip()
        if not cmdline:
            flash(tr("msg.cmd_not_specified"), "warning")
            return redirect(url_for("terminal"))
        workdir = app.config["BASE_DIR"]
        if rel_cwd:
            try:
                workdir = safe_join(app.config["BASE_DIR"], rel_cwd)
            except Exception:
                workdir = app.config["BASE_DIR"]
        try:
            if shell == "powershell":
                command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmdline]
            else:
                command = ["cmd", "/c", cmdline]
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
            hist = session.get("cmd_history", [])
            if cmdline not in hist:
                hist = (hist + [cmdline])[-15:]
            session["cmd_history"] = hist
            return render_template("terminal.html", last_cmd=cmdline, output=output, code=proc.returncode, history=hist, base_dir=app.config["BASE_DIR"])
        except subprocess.TimeoutExpired as e:
            flash(tr("msg.timeout"), "danger")
            return render_template("terminal.html", last_cmd=cmdline, output=str(e), code=None, history=session.get("cmd_history", []), base_dir=app.config["BASE_DIR"])
        except Exception as e:
            flash(tr("msg.exec_error"), "danger")
            return render_template("terminal.html", last_cmd=cmdline, output=str(e), code=None, history=session.get("cmd_history", []), base_dir=app.config["BASE_DIR"])

    @app.route("/terminal/clear", methods=["POST"])
    def terminal_clear():
        session["cmd_history"] = []
        flash(tr("msg.history_cleared"), "success")
        return redirect(url_for("terminal"))

    @app.route("/monitor")
    def monitor():
        return render_template("monitor.html")

    @app.route("/metrics")
    def metrics():
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        cpu_cur = int(cpu_freq.current) if cpu_freq else None
        cpu_max = int(cpu_freq.max) if cpu_freq else None
        # Aggregate disks
        total_disk = 0
        used_disk = 0
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_disk += usage.total
                used_disk += usage.used
            except Exception:
                continue
        disk_percent = round((used_disk / total_disk) * 100, 1) if total_disk else 0
        net = psutil.net_io_counters()
        disk_io = psutil.disk_io_counters()
        gpus = get_gpu_info()
        return jsonify(
            {
                "ts": time.time(),
                "cpu_percent": cpu,
                "cpu_freq_cur": cpu_cur,
                "cpu_freq_max": cpu_max,
                "cpu_cores": psutil.cpu_count(logical=False) or 0,
                "cpu_threads": psutil.cpu_count() or 0,
                "mem_total": mem.total,
                "mem_used": mem.used,
                "mem_percent": mem.percent,
                "mem_available": mem.available,
                "disk_total": total_disk,
                "disk_used": used_disk,
                "disk_percent": disk_percent,
                "net_bytes_sent": net.bytes_sent,
                "net_bytes_recv": net.bytes_recv,
                "disk_read_bytes": getattr(disk_io, "read_bytes", 0),
                "disk_write_bytes": getattr(disk_io, "write_bytes", 0),
                "gpus": gpus,
            }
        )

    # Processes
    @app.route("/processes")
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

    @app.route("/processes/kill", methods=["POST"])
    def processes_kill():
        pid = request.form.get("pid", type=int)
        if not pid:
            flash("PID не указан", "warning")
            return redirect(url_for("processes"))
        try:
            psutil.Process(pid).terminate()
            flash(f"Процесс {pid} завершён", "success")
        except psutil.NoSuchProcess:
            flash("Процесс не найден", "warning")
        except psutil.AccessDenied:
            flash("Нет прав на завершение процесса", "danger")
        except Exception as e:
            flash(f"Ошибка: {e}", "danger")
        return redirect(url_for("processes"))

    # Services (Windows)
    def _parse_sc_query():
        try:
            proc = subprocess.run(["sc", "query", "state=", "all"], capture_output=True, text=True, encoding="cp866", errors="replace")
            lines = proc.stdout.splitlines()
            items = []
            current = {}
            for line in lines:
                if "SERVICE_NAME:" in line:
                    if current:
                        items.append(current)
                    current = {"service_name": line.split("SERVICE_NAME:")[1].strip()}
                elif "DISPLAY_NAME:" in line:
                    current["display_name"] = line.split("DISPLAY_NAME:")[1].strip()
                elif "STATE" in line and ":" in line:
                    state = line.split(":", 1)[1].strip().split("  ")[0].strip()
                    current["state"] = state
            if current:
                items.append(current)
            return items
        except Exception:
            return []

    @app.route("/services")
    def services():
        items = _parse_sc_query()
        return render_template("services.html", services=items)

    @app.route("/services/action", methods=["POST"])
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

    # Ports
    @app.route("/ports")
    def ports():
        entries = []
        pid_name = {}
        try:
            for p in psutil.process_iter(attrs=["pid", "name"]):
                pid_name[p.info["pid"]] = p.info["name"]
        except Exception:
            pass
        try:
            res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="cp866", errors="replace")
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("TCP") or line.startswith("UDP"):
                    parts = [p for p in line.split() if p]
                    if parts[0] == "TCP" and len(parts) >= 5:
                        proto, local, remote, state, pid = parts[0], parts[1], parts[2], parts[3], parts[4]
                    elif parts[0] == "UDP" and len(parts) >= 4:
                        proto, local, remote, state, pid = parts[0], parts[1], parts[2], "-", parts[3]
                    else:
                        continue
                    try:
                        pid_int = int(pid)
                    except Exception:
                        pid_int = None
                    entries.append({"proto": proto, "local": local, "remote": remote, "state": state, "pid": pid_int, "name": pid_name.get(pid_int)})
        except Exception:
            pass
        return render_template("ports.html", entries=entries[:500])

    # Network
    @app.route("/network", methods=["GET", "POST"])
    def network():
        if request.method == "POST":
            host = request.form.get("host", "").strip()
            out = ""
            if host:
                try:
                    res = subprocess.run(["ping", "-n", "4", host], capture_output=True, text=True, encoding="cp866", errors="replace", timeout=20)
                    out = res.stdout or res.stderr
                except Exception as e:
                    out = str(e)
            return render_template("network.html", ifaces=psutil.net_if_addrs(), ping_host=host, ping_out=out)
        return render_template("network.html", ifaces=psutil.net_if_addrs(), ping_host=None, ping_out=None)

    # Disks and directory sizes
    def _dir_sizes(path, max_items=30):
        items = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_file():
                            size = entry.stat().st_size
                        elif entry.is_dir():
                            size = 0
                            with os.scandir(entry.path) as it2:
                                for e2 in it2:
                                    try:
                                        if e2.is_file():
                                            size += e2.stat().st_size
                                    except Exception:
                                        continue
                        else:
                            size = 0
                        items.append({"name": entry.name, "is_dir": entry.is_dir(), "size": size})
                    except Exception:
                        continue
        except Exception:
            pass
        items.sort(key=lambda x: x["size"], reverse=True)
        return items[:max_items]

    @app.route("/disks")
    def disks():
        parts = []
        for p in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(p.mountpoint)
                parts.append({"device": p.device, "mount": p.mountpoint, "fstype": p.fstype, "total": u.total, "used": u.used, "percent": u.percent})
            except Exception:
                continue
        path = request.args.get("path")
        du_items = None
        if path:
            try:
                target = path if os.path.isabs(path) else os.path.join(app.config["BASE_DIR"], path)
                du_items = _dir_sizes(target)
            except Exception:
                du_items = None
        return render_template("disks.html", parts=parts, du_path=path, du_items=du_items)

    # System Info
    @app.route("/system")
    def system_info():
        import platform, getpass
        info = {
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "python": platform.python_version(),
            "user": getpass.getuser(),
            "boot_time": psutil.boot_time(),
            "cpu_count": psutil.cpu_count(),
            "cpu_count_phys": psutil.cpu_count(logical=False),
            "mem": psutil.virtual_memory()._asdict(),
        }
        return render_template("system.html", info=info)

    # Scheduled Tasks
    def _schtasks_list():
        tasks = []
        try:
            res = subprocess.run(["schtasks", "/Query", "/FO", "CSV"], capture_output=True, text=True, encoding="cp866", errors="replace")
            if res.returncode == 0:
                import csv, io
                reader = csv.DictReader(io.StringIO(res.stdout))
                for row in reader:
                    tasks.append({"name": row.get("TaskName"), "status": row.get("Status"), "next_run": row.get("Next Run Time")})
        except Exception:
            pass
        return tasks

    @app.route("/tasks", methods=["GET", "POST"])
    def tasks():
        if request.method == "POST":
            name = request.form.get("name", "")
            if name:
                try:
                    res = subprocess.run(["schtasks", "/Run", "/TN", name], capture_output=True, text=True, encoding="cp866", errors="replace")
                    if res.returncode == 0:
                        flash("Задание запущено", "success")
                    else:
                        flash(res.stdout or res.stderr, "danger")
                except Exception as e:
                    flash(str(e), "danger")
        return render_template("tasks.html", tasks=_schtasks_list())

    # Logs tail
    def _tail(path, lines=200):
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                block = 4096
                data = b""
                while size > 0 and data.count(b"\n") <= lines:
                    read_size = min(block, size)
                    size -= read_size
                    f.seek(size)
                    data = f.read(read_size) + data
                text = data.decode("utf-8", errors="replace")
                return "\n".join(text.splitlines()[-lines:])
        except Exception:
            return ""

    @app.route("/logs", methods=["GET", "POST"])
    def logs():
        root = app.config["BASE_DIR"]
        chosen = request.form.get("path") if request.method == "POST" else request.args.get("path")
        content = None
        if chosen:
            try:
                target = safe_join(root, chosen)
                content = _tail(target, lines=400)
            except Exception:
                content = None
        candidates = []
        for dirpath, dirnames, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in [".log", ".txt"]:
                    p = os.path.join(rel if rel != "." else "", fn).replace("\\", "/")
                    candidates.append(p)
            if len(candidates) > 500:
                break
        candidates = sorted(candidates)[:500]
        return render_template("logs.html", files=candidates, path=chosen, content=content)

    # Backup zip
    @app.route("/backup", methods=["GET", "POST"])
    def backup():
        if request.method == "POST":
            rel = request.form.get("path", "")
            try:
                target = safe_join(app.config["BASE_DIR"], rel)
            except Exception:
                flash("Недопустимый путь", "danger")
                return redirect(url_for("backup"))
            import io, zipfile
            max_bytes = 100 * 1024 * 1024
            total = 0
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                if os.path.isfile(target):
                    total += os.path.getsize(target)
                    if total > max_bytes:
                        flash("Размер архива превышает лимит 100MB", "danger")
                        return redirect(url_for("backup"))
                    zf.write(target, arcname=os.path.basename(target))
                else:
                    for dirpath, dirnames, filenames in os.walk(target):
                        for fn in filenames:
                            fp = os.path.join(dirpath, fn)
                            try:
                                total += os.path.getsize(fp)
                                if total > max_bytes:
                                    flash("Размер архива превышает лимит 100MB", "danger")
                                    return redirect(url_for("backup"))
                                arc = os.path.relpath(fp, os.path.dirname(target))
                                zf.write(fp, arcname=arc)
                            except Exception:
                                continue
            buf.seek(0)
            name = (os.path.basename(target) or "backup") + ".zip"
            return send_file(buf, as_attachment=True, download_name=name, mimetype="application/zip")
        return render_template("backup.html")

    # Power (requires env ALLOW_POWER=1)
    @app.route("/power", methods=["GET", "POST"])
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

    @app.route("/scripts")
    def scripts():
        scripts_root = app.config["SCRIPTS_DIR"]
        os.makedirs(scripts_root, exist_ok=True)
        entries = []
        for name in os.listdir(scripts_root):
            full = os.path.join(scripts_root, name)
            if os.path.isfile(full) and os.path.splitext(name)[1].lower() in [".py", ".bat"]:
                entries.append({"name": name})
        return render_template("scripts.html", scripts=sorted(entries, key=lambda x: x["name"].lower()))

    @app.route("/run", methods=["POST"])
    def run_script():
        script_name = request.form.get("script")
        args_line = request.form.get("args", "").strip()
        if not script_name:
            flash(tr("msg.script_not_chosen"), "warning")
            return redirect(url_for("scripts"))
        scripts_root = app.config["SCRIPTS_DIR"]
        script_path = safe_join(scripts_root, secure_filename(script_name))
        if not os.path.isfile(script_path):
            flash(tr("msg.script_not_found"), "danger")
            return redirect(url_for("scripts"))

        ext = pathlib.Path(script_path).suffix.lower()
        if ext not in [".py", ".bat"]:
            flash(tr("msg.only_py_bat"), "danger")
            return redirect(url_for("scripts"))

        if args_line:
            extra_args = args_line.split()
        else:
            extra_args = []

        if ext == ".py":
            cmd = [sys.executable, script_path] + extra_args
        else:
            cmd = ["cmd", "/c", script_path] + extra_args

        try:
            proc = subprocess.run(
                cmd,
                cwd=os.path.dirname(script_path),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )
            output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            return render_template(
                "run_result.html",
                script=os.path.basename(script_path),
                code=proc.returncode,
                output=output,
            )
        except Exception as e:
            flash(f"{tr('msg.script_error')}: {e}", "danger")
            return redirect(url_for("scripts"))

    @app.route("/lang/<lang>")
    def set_lang(lang):
        if lang not in SUPPORTED_LANGS:
            lang = "ru"
        session["lang"] = lang
        next_url = flask_request.args.get("next")
        if next_url:
            return redirect(next_url)
        ref = flask_request.headers.get("Referer")
        if ref:
            return redirect(ref)
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", "5000"))
    debug_flag = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_flag, use_reloader=debug_flag)

