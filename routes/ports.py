import subprocess
import psutil
from flask import render_template

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
