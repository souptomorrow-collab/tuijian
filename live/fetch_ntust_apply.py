# -*- coding: utf-8 -*-
"""重抓台科 116 碩士班甄試「即時報名人數統計表」,重寫 data/apply_ntust.md(之後執行 tools/inject_apply.py 放進網頁)。
官方頁是伺服器端產生的 HTML,直接 GET 就有數字;115 欄是已結束的最終數字,寫死在下面。
用法: python tools/fetch_ntust_apply.py [輸出檔]  (工作目錄任意;不給輸出檔就寫 data/apply_ntust.md)
GitHub Actions(public/.github/workflows/apply-live.yml)每 15 分鐘也跑這支(make_public.py 會複製到 public/live/),
網頁打開時讀 live 分支的 apply_live.json,比內嵌的新就換上。查詢時間一律用台灣時間(Actions 設 TZ=Asia/Taipei)。
"""
import datetime, io, os, re, sys, urllib.request

URL116 = "https://entrance.ntust.edu.tw/16entry1/Statistics.aspx"
URL115 = "https://entrance.ntust.edu.tw/15entry1/Statistics.aspx"
# (系所組別, 代碼, 116 名額顯示, 116 名額, 115 完成報名, 115 名額);名額取自 data/ntust.md(116 簡章)
ROWS = [
    ("電機系 AI組(外加名額)", "0700", "5", 5, 70, 5),
    ("電機系 甲組(電力與能源)", "0710", "29", 29, 131, 30),
    ("電機系 乙組(電力電子)", "0720", "16", 16, 151, 17),
    ("電機系 丙組(系統工程)", "0730", "17", 17, 182, 15),
    ("電機系 丁組(積體電路與系統)", "0740", "23", 23, 242, 21),
    ("電機系 戊組(資訊與通訊)", "0750", "12", 12, 140, 12),
    ("電機系 己一組(通訊與網路)", "0761", "11", 11, 103, 12),
    ("電機系 己二組(電波工程)", "0762", "8", 8, 63, 8),
    ("電子系 甲組", "0210", "42", 42, 218, 42),
    ("電子系 乙一組", "0221", "43", 43, 229, 43),
    ("電子系 乙二組(電力電子及電路)", "0222", "24", 24, 227, 24),
    ("電子系 丙組", "0230", "32", 32, 239, 32),
    ("光電所", "1900", "16", 16, 219, 16),
    ("自控所", "1200", "31", 31, 189, 20),
]
DEADLINE = datetime.datetime(2026, 10, 6, 17, 0)      # 報名截止 115/10/6 17:00
SETTLED = datetime.datetime(2026, 10, 13)             # 繳費截止後約 4 個工作天
LIVE_END = datetime.datetime(2026, 10, 20)            # 之後 GitHub Actions 不再每 15 分鐘更新


def r1(x):
    """四捨五入到 1 位小數(不用 Python 的銀行家捨入)"""
    return "%.1f" % (int(x * 10 + 0.5) / 10.0)


req = urllib.request.Request(URL116, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
now = datetime.datetime.now()
got = {}
for _, code, *_ in ROWS:
    m = re.search(r"\b%s\b\s+\S+\s+(\d+)\s+(\d+)" % code, text)
    assert m, "官方頁找不到代碼 %s(版面可能改了)" % code
    got[code] = (int(m.group(1)), int(m.group(2)))

if now < DEADLINE:
    status = "**狀態:報名中,官方即時統計(浮動)**。報名 115/9/30 09:00–10/6 17:00,繳費同日 24:00 截止。"
elif now < SETTLED:
    status = "**狀態:報名已截止(10/6 17:00),官方仍在查核繳費,數字為浮動人數**。"
else:
    status = "**狀態:報名已截止,官方查核期已過**;以下為官方統計表目前數字,正式人數以官方公告為準。"
upd = "查詢時間 %s" % now.strftime("%Y-%m-%d %H:%M")
upd += ";報名期間網頁會定時自動重抓官方數字,實際間隔視 GitHub 排程而定(約 15 分鐘到數小時)。" if now < LIVE_END else "。"

out = ["# 台科大 116 學年度碩士班甄試報名人數", "",
       "> " + status,
       "> **人數怎麼算**:「116報名」是官方「即時報名人數統計表」的「完成報名作業人數」;「116未完成」是還沒完成報名手續的人,不算進倍數。官方說明表內是浮動人數,繳費截止後約 4 個工作天(約 10/13 前後)才是正確報名人數。",
       "> **更新時間**:" + upd, "",
       "**怎麼看「倍數」**:倍數 = 報名人數 ÷ 名額,也就是平均每個名額有幾個人報名,數字越大越競爭。"
       "例如 115 電機系甲組 30 個名額、131 人報名,131 ÷ 30 ≈ 4.4 倍。116 的倍數是用查詢當時的人數算的,官方查核完成前還會變動。"
       "倍數不是錄取率:很多人同時報好幾校,錄取後放棄的名額會由備取遞補,實際錄取難度通常比倍數看起來低;"
       "各校公布的人數種類也不同,跨校比較只能看大概。", "",
       "| 系所組別 | 代碼 | 116名額 | 116報名 | 116未完成 | 116倍數 | 115名額 | 115報名 | 115倍數 |",
       "|---|---|---|---|---|---|---|---|---|"]
for name, code, qs, q, y115, q115 in ROWS:
    done, undone = got[code]
    out.append("| %s | %s | %s | %d | %d | %s | %d | %d | %s |" % (name, code, qs, done, undone, r1(done / q), q115, y115, r1(y115 / q115)))
out += ["",
        "- 116 報名比 115 晚 5 天開始(115 為 9/25–10/2);報名截止前和 115 的最終數字相比會偏低。",
        "- 115 欄取自同一系統的 115 統計表,報名早已結束,即為最終數字;116 名額取自 116 簡章(見「簡章」分頁)。",
        "- 來源:[116 即時報名人數統計表](%s)、[115 即時報名人數統計表](%s)。" % (URL116, URL115), ""]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "data", "apply_ntust.md")
io.open(dst, "w", encoding="utf-8").write("\n".join(out))
print("apply_ntust 已更新:", now.strftime("%Y-%m-%d %H:%M"), "| 電機甲組 完成 %d、未完成 %d" % got["0710"])
