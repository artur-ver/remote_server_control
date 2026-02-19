import os
import mimetypes
import zipfile
import io
import shutil
import json
import time
from flask import current_app, request, abort, flash, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
from utils import safe_join, is_text_file
from i18n import tr

def get_trash_dir():
    base = current_app.config["BASE_DIR"]
    t_dir = os.path.join(base, ".trash")
    if not os.path.exists(t_dir):
        os.makedirs(t_dir)
    return t_dir

def get_trash_map_file():
    return os.path.join(get_trash_dir(), "restore_map.json")

def load_trash_map():
    f = get_trash_map_file()
    if not os.path.exists(f):
        return {}
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except:
        return {}

def save_trash_map(data):
    f = get_trash_map_file()
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)

def browse():
    rel_path = request.args.get("path", "")
    current_path = safe_join(current_app.config["BASE_DIR"], rel_path)
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
                        "rel_path": os.path.relpath(full, current_app.config["BASE_DIR"]),
                        "ext": os.path.splitext(name)[1].lower() if os.path.isfile(full) else "",
                    }
                )
        except PermissionError:
            flash(tr("msg.no_access"), "warning")
            items = []

        parent_rel = None
        rel_norm = os.path.relpath(current_path, current_app.config["BASE_DIR"])
        if rel_norm != ".":
            parent_rel = os.path.relpath(os.path.dirname(current_path), current_app.config["BASE_DIR"])
        return render_template(
            "files.html",
            items=sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower())),
            current_rel="" if rel_norm == "." else rel_norm,
            parent_rel=parent_rel if parent_rel != "." else "",
        )
    else:
        return redirect(url_for("view_file", path=rel_path))

def upload():
    rel_path = request.form.get("path", "")
    current_path = safe_join(current_app.config["BASE_DIR"], rel_path)
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

def view_file():
    rel_path = request.args.get("path", "")
    file_path = safe_join(current_app.config["BASE_DIR"], rel_path)
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
        rel_path=os.path.relpath(file_path, current_app.config["BASE_DIR"]),
        is_text=text is not None,
        text_content=text,
    )

def edit_file():
    rel_path = request.args.get("path") if request.method == "GET" else request.form.get("path")
    if not rel_path:
        abort(400)
    file_path = safe_join(current_app.config["BASE_DIR"], rel_path)
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
        return render_template("edit.html", rel_path=os.path.relpath(file_path, current_app.config["BASE_DIR"]), text_content=text)

def download_file():
    rel_path = request.args.get("path", "")
    file_path = safe_join(current_app.config["BASE_DIR"], rel_path)
    if not os.path.isfile(file_path):
        abort(404)
    mime, _ = mimetypes.guess_type(file_path)
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path), mimetype=mime)

def backup():
    if request.method == "POST":
        rel = request.form.get("path", "")
        try:
            target = safe_join(current_app.config["BASE_DIR"], rel)
        except Exception:
            flash(tr("backup.invalid_path"), "danger")
            return redirect(url_for("backup"))
        max_bytes = 100 * 1024 * 1024
        total = 0
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if os.path.isfile(target):
                total += os.path.getsize(target)
                if total > max_bytes:
                    flash(tr("backup.limit_exceeded"), "danger")
                    return redirect(url_for("backup"))
                zf.write(target, arcname=os.path.basename(target))
            else:
                for dirpath, dirnames, filenames in os.walk(target):
                    for fn in filenames:
                        fp = os.path.join(dirpath, fn)
                        try:
                            total += os.path.getsize(fp)
                            if total > max_bytes:
                                flash(tr("backup.limit_exceeded"), "danger")
                                return redirect(url_for("backup"))
                            arc = os.path.relpath(fp, os.path.dirname(target))
                            zf.write(fp, arcname=arc)
                        except Exception:
                            continue
        buf.seek(0)
        name = (os.path.basename(target) or "backup") + ".zip"
        return send_file(buf, as_attachment=True, download_name=name, mimetype="application/zip")
    return render_template("backup.html")

def trash_list():
    t_dir = get_trash_dir()
    t_map = load_trash_map()
    items = []

    if os.path.exists(t_dir):
        for name in os.listdir(t_dir):
            if name == "restore_map.json": continue
            full = os.path.join(t_dir, name)

            info = t_map.get(name, {})
            original_path = info.get("original_path", "???") if isinstance(info, dict) else "???"
            deleted_at = info.get("deleted_at", 0) if isinstance(info, dict) else 0

            items.append({
                "name": name,
                "display_name": os.path.basename(original_path),
                "original_path": original_path,
                "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                "is_dir": os.path.isdir(full),
                "deleted_at": deleted_at,
                "date_str": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deleted_at)) if deleted_at else "-"
            })

    return render_template("trash.html", items=sorted(items, key=lambda x: x["deleted_at"], reverse=True))

def trash_add():
    rel_path = request.args.get("path")
    if not rel_path:
        flash(tr("msg.not_found"), "danger")
        return redirect(url_for("browse"))
    
    full_path = safe_join(current_app.config["BASE_DIR"], rel_path)
    if not os.path.exists(full_path):
        flash(tr("msg.not_found"), "danger")
        return redirect(url_for("browse"))
        
    t_dir = get_trash_dir()
    name = os.path.basename(full_path)
    trash_name = f"{int(time.time())}_{name}"
    trash_path = os.path.join(t_dir, trash_name)
    
    try:
        shutil.move(full_path, trash_path)
        t_map = load_trash_map()
        t_map[trash_name] = {
            "original_path": rel_path,
            "deleted_at": time.time()
        }
        save_trash_map(t_map)
        flash(tr("msg.moved_to_trash"), "success")
    except Exception as e:
        flash(f"{tr('msg.error')}: {str(e)}", "danger")
        
    return redirect(url_for("browse", path=os.path.dirname(rel_path).replace("\\", "/")))

def trash_restore():
    name = request.form.get("name")
    if not name: return redirect(url_for("trash_list"))
    
    t_dir = get_trash_dir()
    try:
        source = safe_join(t_dir, name)
    except:
        flash(tr("msg.not_found"), "danger")
        return redirect(url_for("trash_list"))
    
    if not os.path.exists(source):
        flash(tr("msg.not_found"), "danger")
        return redirect(url_for("trash_list"))
        
    t_map = load_trash_map()
    info = t_map.get(name)
    if not info:
        flash(tr("msg.restore_error"), "danger")
        return redirect(url_for("trash_list"))
        
    orig_rel = info.get("original_path")
    if not orig_rel:
        flash(tr("msg.restore_error"), "danger")
        return redirect(url_for("trash_list"))

    dest = safe_join(current_app.config["BASE_DIR"], orig_rel)
    
    if os.path.exists(dest):
        flash(tr("msg.restore_collision"), "warning")
        return redirect(url_for("trash_list"))
        
    try:
        parent = os.path.dirname(dest)
        if not os.path.exists(parent):
            os.makedirs(parent)
            
        shutil.move(source, dest)
        del t_map[name]
        save_trash_map(t_map)
        flash(tr("msg.restored"), "success")
    except Exception as e:
        flash(f"{tr('msg.error')}: {str(e)}", "danger")
        
    return redirect(url_for("trash_list"))

def trash_delete():
    name = request.form.get("name")
    if not name: return redirect(url_for("trash_list"))

    t_dir = get_trash_dir()
    try:
        path = safe_join(t_dir, name)
    except:
        flash(tr("msg.not_found"), "danger")
        return redirect(url_for("trash_list"))
    
    # Try to delete file/dir if it exists
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            flash(f"{tr('msg.error')}: {str(e)}", "danger")
            return redirect(url_for("trash_list"))

    # Remove from map (even if file was already gone)
    t_map = load_trash_map()
    if name in t_map:
        del t_map[name]
        save_trash_map(t_map)
        
    flash(tr("msg.deleted"), "success")    
    return redirect(url_for("trash_list"))

def trash_empty():
    t_dir = get_trash_dir()
    if os.path.exists(t_dir):
        # We'll try to delete contents one by one to avoid locking issues with the folder itself
        try:
            for name in os.listdir(t_dir):
                path = os.path.join(t_dir, name)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception:
                    # If we can't delete one item, continue with others
                    pass
            
            # Reset the map
            save_trash_map({})
            flash(tr("msg.trash_emptied"), "success")
        except Exception as e:
            flash(f"{tr('msg.error')}: {str(e)}", "danger")
            
    return redirect(url_for("trash_list"))
