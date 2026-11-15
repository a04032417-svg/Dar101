#!/usr/bin/env python3
"""gs_links.py <src.zip> <dst.zip> <ids.json> "<Suite Name>"
ids.json = [["01 - Part folder name", "<google sheet id>"], ...] (8 items, ZIP folder names).
Adds Google-Sheets-copy-links.txt (Make a copy links) and fixes the top README format line."""
import zipfile, sys, json
src, dst, idf, suite = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
ids = json.load(open(idf))
gs = [f"{suite} - Google Sheets copies", "",
      "Open a link while signed in to your Google account and press \"Make a copy\".",
      "The copy is yours, saved in your own Google Drive; nobody else can see it.", ""]
for n, i in ids:
    gs += [n, f"  https://docs.google.com/spreadsheets/d/{i}/copy", ""]
gs += ["Each copy is the blank workbook. To see the sample data in Google Sheets,",
       "upload the _DEMO-sample-data.xlsx file to Google Drive and open it with Google Sheets.", "",
       "Note: Google Sheets does not keep the formula-cell lock of the .xlsx file.",
       "Type only in the yellow and white cells; gray cells calculate by themselves.", ""]
zi = zipfile.ZipFile(src); zo = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9)
for it in zi.infolist():
    data = zi.read(it.filename)
    if it.filename == "README.txt":
        t = data.decode("utf8"); nl = "\r\n" if "\r\n" in t else "\n"
        old = "Standard .xlsx files for Microsoft Excel and LibreOffice Calc. No macros. "
        if old in t:
            t = t.replace(old, "Standard .xlsx files for Microsoft Excel, Google Sheets and LibreOffice Calc. No macros." + nl +
                          "Google Sheets: open Google-Sheets-copy-links.txt and press \"Make a copy\" on each link." + nl)
        data = t.encode("utf8")
    zo.writestr(it, data, compress_type=zipfile.ZIP_DEFLATED)
zo.writestr(zipfile.ZipInfo("Google-Sheets-copy-links.txt", date_time=zi.infolist()[0].date_time),
            "\r\n".join(gs).encode("utf8"), compress_type=zipfile.ZIP_DEFLATED)
zo.close(); print("ok", dst)
