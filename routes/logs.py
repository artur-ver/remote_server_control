import os
from flask import current_app, render_template, request
from utils import safe_join, tail_file

def logs():
    root = current_app.config["BASE_DIR"]
    chosen = request.form.get("path") if request.method == "POST" else request.args.get("path")
    content = None
    if chosen:
        try:
            target = safe_join(root, chosen)
            content = tail_file(target, lines=400)
        except Exception:
            content = None
    candidates = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in [".log", ".txt"]:
                full = os.path.join(dirpath, fn)
                try:
                    st = os.stat(full)
                    candidates.append({
                        "path": os.path.join(rel if rel != "." else "", fn).replace("\\", "/"),
                        "size": st.st_size,
                        "mtime": st.st_mtime
                    })
                except Exception:
                    continue
        if len(candidates) > 500:
            break
    candidates.sort(key=lambda x: x["mtime"], reverse=True)
    return render_template("logs.html", files=candidates[:500], path=chosen, content=content)
