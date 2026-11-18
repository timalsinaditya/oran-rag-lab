"""REPORT.md -> REPORT.html -> REPORT.docx (LibreOffice). Images embedded; screenshot placeholders highlighted."""
import base64, re, subprocess, sys
from markdown_it import MarkdownIt
md = open("REPORT.md").read()
md = re.sub(r"^(\*\*Figure \d+\.\*\*.*)$", r'<p class="cap">\1</p>', md, flags=re.M)
html = MarkdownIt("commonmark").enable("table").render(md)
html = re.sub(r'<p class="cap">\*\*(Figure \d+\.)\*\*', r'<p class="cap"><b>\1</b>', html)
def embed(m):
    src, alt = m.group(2), m.group(1)
    data = base64.b64encode(open(src, "rb").read()).decode()
    return f'<p class="fig"><img src="data:image/png;base64,{data}" alt="{alt}" width="620"></p>'
html = re.sub(r'<p><img src="([^"]+)" alt="([^"]*)" ?/?></p>', lambda m: embed(re.match(r'(.*)', m.group(2)) and type("M", (), {"group": lambda self, i: (m.group(2), m.group(1))[i - 1]})()), html)
html = html.replace("<table>", '<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse">')
html = re.sub(r"<blockquote>\s*<p><strong>\[(SCREENSHOT[^<]*)\]</strong></p>\s*</blockquote>",
              r'<p class="shot">[\1]</p>', html)
css = """body{font-family:'Times New Roman',serif;font-size:11pt;line-height:1.35}
h1{font-size:17pt;text-align:center}h2{font-size:13pt;margin-top:16pt}h3{font-size:11.5pt}
table{border-collapse:collapse;margin:6pt 0;font-size:9.5pt}th,td{border:1px solid #777;padding:3pt 5pt;vertical-align:top}
th{background:#e8edf3}code{font-family:'Courier New',monospace;font-size:9pt}
.fig{text-align:center}.cap{font-size:9.5pt;text-align:center;font-style:italic}
.shot{background:#fff3b0;border:1px dashed #b38f00;padding:6pt;font-size:10pt}"""
open("REPORT.html", "w").write(f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{html}</body></html>")
r = subprocess.run(["soffice", "--headless", "--convert-to", "docx:MS Word 2007 XML", "REPORT.html", "--outdir", "."],
                   capture_output=True, text=True, timeout=180)
print(r.stdout.strip() or r.stderr.strip())
