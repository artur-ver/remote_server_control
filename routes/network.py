import subprocess
import psutil
from flask import render_template, request

def network():
    ping_host = None
    ping_out = None
    if request.method == "POST":
        host = request.form.get("host", "").strip()
        if host:
            ping_host = host
            try:
                res = subprocess.run(["ping", "-n", "4", host], capture_output=True, text=True, encoding="cp866", errors="replace", timeout=20)
                ping_out = res.stdout or res.stderr
            except Exception as e:
                ping_out = str(e)
    
    # Flatten interfaces for table
    ifaces_data = []
    try:
        for name, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                fam = str(a.family)
                if "AF_INET" in fam: fam = "IPv4"
                elif "AF_INET6" in fam: fam = "IPv6"
                elif "AF_LINK" in fam: fam = "MAC"
                ifaces_data.append({
                    "interface": name,
                    "family": fam,
                    "address": a.address,
                    "netmask": a.netmask or ""
                })
    except Exception:
        pass
    ifaces_data.sort(key=lambda x: x["interface"])
        
    return render_template("network.html", ifaces=ifaces_data, ping_host=ping_host, ping_out=ping_out)
