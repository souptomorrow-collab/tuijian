# -*- coding: utf-8 -*-
"""GitHub Actions(.github/workflows/apply-live.yml)用:跑同資料夾的 fetch_ntust_apply.py、fetch_yuntech_apply.py,
把兩份 markdown 包成 apply_live.json,由 workflow 推到 live 分支;網頁(index.html 與 private/)打開時讀這個檔。
抓取程式的正本在本機 推甄資料/tools/,make_public.py 每次會複製過來,不要直接改這裡的副本。
2026-10-20 之後不再產生(兩校報名與查核都已結束)。
用法: python3 live/build_live.py <輸出 json>
"""
import datetime, io, json, os, subprocess, sys, tempfile

END = datetime.datetime(2026, 10, 20)
here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else "apply_live.json"
now = datetime.datetime.now()
if now >= END:
    print("live update period ended")
    sys.exit(0)

data = {"generated": now.strftime("%Y-%m-%d %H:%M")}
tmp = tempfile.mkdtemp()
for k in ("ntust", "yuntech"):
    md = os.path.join(tmp, k + ".md")
    r = subprocess.run([sys.executable, os.path.join(here, "fetch_%s_apply.py" % k), md], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print(k, "exit", r.returncode, (r.stdout + r.stderr).strip()[-400:])
    if r.returncode == 0 and os.path.exists(md):
        data[k] = io.open(md, encoding="utf-8").read()
if len(data) == 1:
    sys.exit("both schools failed")          # 兩校都抓不到就不推,網頁沿用上一版
io.open(out, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
print("wrote", out, sorted(data))
