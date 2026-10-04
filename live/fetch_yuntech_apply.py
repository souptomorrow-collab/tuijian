# -*- coding: utf-8 -*-
"""重抓雲科 116 碩士班甄試「網路報名人數即時查詢」,重寫 data/apply_yuntech.md(之後執行 tools/inject_apply.py 放進網頁)。
官方頁是伺服器端產生的 HTML,直接 GET 就有數字;115 欄是同一頁 115 學年度的最終數字,寫死在下面。
網頁「保底四校」的報名人數分頁 = apply_yuntech.md(本程式產生)+ apply_other.md(高科/元智/淡江,手動維護)。
用法: python tools/fetch_yuntech_apply.py [輸出檔]  (工作目錄任意;不給輸出檔就寫 data/apply_yuntech.md)
GitHub Actions 每 15 分鐘也跑這支(說明見 fetch_ntust_apply.py)。
"""
import datetime, io, os, re, sys, urllib.request

URL116 = "https://examweb.yuntech.edu.tw/WebExams/QueryInfo/qExamRegCounts.aspx?acadyear=116&examtype=S"
URL115 = "https://examweb.yuntech.edu.tw/WebExams/QueryInfo/qExamRegCounts.aspx?acadyear=115&examtype=S"
# (系所組別, 代碼, 115 完成繳費人數, 115 名額);組名取自 data/others.md(116 簡章),115 數字取自上面 115 頁
ROWS = [
    ("電機系 甲組(電力系統與電力電子)", "12111", 74, 8),
    ("電機系 乙組(自動化與系統控制)", "12121", 111, 14),
    ("電機系 丙組(資訊與通訊)", "12131", 104, 17),
    ("電機系 丁組(積體電路與系統設計)", "12141", 76, 14),
    ("電機系 戊組(產業組)", "12151", 32, 9),
]
DEADLINE = datetime.datetime(2026, 10, 16, 0, 0)      # 報名 115/9/29 09:00–10/15 23:59
QUERY_END = datetime.datetime(2026, 10, 16, 17, 0)    # 即時查詢開放到 10/16 17:00
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
    # 欄位:招生名額、完成繳費人數、已完成系統報名及繳費人數、(系合計)、上傳資料及完成報名人數、(系合計);系合計只出現在各系第一列
    m = re.search(r"\b%s\b((?:\s+\d+)+)" % code, text)
    assert m, "官方頁找不到代碼 %s(版面可能改了)" % code
    nums = [int(x) for x in m.group(1).split()]
    assert len(nums) in (4, 6), "代碼 %s 的欄位數不對: %s" % (code, nums)
    q, paid, upload = nums[0], nums[1], nums[4] if len(nums) == 6 else nums[3]
    got[code] = (q, paid, upload)

if now < DEADLINE:
    status = "**狀態:報名中,官方即時統計(浮動)**。報名 115/9/29 09:00–10/15 23:59;官方即時查詢開放到 10/16 17:00。"
elif now < QUERY_END:
    status = "**狀態:報名已截止(10/15 23:59)**;官方即時查詢開放到 10/16 17:00,之後同一頁的數字即為最終數字。"
else:
    status = "**狀態:報名已截止**;以下為官方查詢頁目前數字(115 學年度的同一頁在報名結束後一直維持最終數字)。"
upd = "查詢時間 %s" % now.strftime("%Y-%m-%d %H:%M")
upd += ";報名期間網頁每 15 分鐘自動重抓一次。" if now < LIVE_END else "。"

out = ["# 雲科 116 學年度碩士班甄試報名人數", "",
       "> " + status,
       "> **人數怎麼算**:官方說明「已確定繳費者，始列計報考人數」,所以「116報名」用「完成繳費人數」;「116已上傳」是已經上傳審查資料、完成報名的人數。",
       "> **更新時間**:" + upd, "",
       "**怎麼看「倍數」**:倍數 = 報名人數 ÷ 名額,也就是平均每個名額有幾個人報名,數字越大越競爭。"
       "例如 115 電機系甲組(電力系統與電力電子)8 個名額、74 人報名,74 ÷ 8 ≈ 9.3 倍。116 的倍數是用查詢當時的人數算的,報名結束前還會變動。"
       "倍數不是錄取率:很多人同時報好幾校,錄取後放棄的名額會由備取遞補,實際錄取難度通常比倍數看起來低;"
       "各校公布的人數種類也不同,跨校比較只能看大概。", "",
       "| 系所組別 | 代碼 | 116名額 | 116報名 | 116已上傳 | 116倍數 | 115名額 | 115報名 | 115倍數 |",
       "|---|---|---|---|---|---|---|---|---|"]
tq = tp = tu = ty = tq115 = 0
for name, code, y115, q115 in ROWS:
    q, paid, upload = got[code]
    out.append("| %s | %s | %d | %d | %d | %s | %d | %d | %s |" % (name, code, q, paid, upload, r1(paid / q), q115, y115, r1(y115 / q115)))
    tq += q; tp += paid; tu += upload; ty += y115; tq115 += q115
out.append("| 電機系合計 | — | %d | %d | %d | %s | %d | %d | %s |" % (tq, tp, tu, r1(tp / tq), tq115, ty, r1(ty / tq115)))
out += ["",
        "- 116 名額取自官方查詢頁的「招生名額」欄(與 116 簡章相同)。",
        "- 115 欄取自同一系統的 115 查詢頁,報名早已結束,該頁的完成繳費人數即為最終數字。",
        "- 來源:[116 網路報名人數即時查詢](%s)、[115 網路報名人數查詢](%s)。" % (URL116, URL115), ""]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "data", "apply_yuntech.md")
io.open(dst, "w", encoding="utf-8").write("\n".join(out))
print("apply_yuntech 已更新:", now.strftime("%Y-%m-%d %H:%M"), "| 電機甲組 完成繳費 %d" % got["12111"][1])
