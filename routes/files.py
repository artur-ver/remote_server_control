import os
import mimetypes
import zipfile
import io
from flask import current_app, request, abort, flash, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
from utils import safe_join, is_text_file
from i18n import tr

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
            flash("Недопустимый путь", "danger")
            return redirect(url_for("backup"))
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
