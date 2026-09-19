#!/usr/bin/env python3
"""Inventory Xiao et al. 2025 original Table/Data S1–S3 without guessed labels.

Uses original OA ZIP with source hash; writes small, reviewable sheet summaries.
Produces full raw-cell CSVs only as ephemeral workflow artifacts, not commits.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from xml.etree import ElementTree as ET
from pathlib import Path
from openpyxl import load_workbook

ZIP_SHA="132f3d2c2d6c8a5fcb102fe9dcfa5e2d33c6e60b6600c1c94d0d2bafb282c233"
PRODUCT=re.compile(r"\bM\d{8,13}[A-Z]{0,4}\b",re.I)

def main():
    record=json.loads(Path("diagnostics/isef4_published_s5_source_status.json")
                      .read_text().replace("\\n",""))
    if record["sha256"] != ZIP_SHA:raise ValueError("published source changed")
    req=urllib.request.Request(record["source_url"],headers={
        "User-Agent":"LUNARSHIFT-source-spreadsheet-inventory/1.0"})
    with urllib.request.urlopen(req,timeout=120) as response:
        blob=response.read(40_000_001)
    if len(blob)>40_000_000 or hashlib.sha256(blob).hexdigest()!=ZIP_SHA:
        raise RuntimeError("official source ZIP did not verify")
    with zipfile.ZipFile(io.BytesIO(blob)) as outer:
        names=[x for x in outer.namelist() if x.endswith(".xlsx")]
        if len(names)!=1:raise RuntimeError("not exactly one original source workbook")
        xlsx=outer.read(names[0])
        docx_names=[x for x in outer.namelist() if x.lower().endswith('.docx')]
        if len(docx_names)!=1:raise RuntimeError('not exactly one original Word supplement')
        docx_blob=outer.read(docx_names[0])
    book=load_workbook(io.BytesIO(xlsx),read_only=True,data_only=True)
    output=Path("output/isef4_original_xiao_tables")
    output.mkdir(parents=True,exist_ok=True)
    sheets=[]
    for sheet in book.worksheets:
        name=re.sub(r"[^a-zA-Z0-9_-]+","_",sheet.title)
        dest=output/(name+".csv")
        sample=[]
        products=set()
        product_occurrences=0
        populated=0
        with dest.open("w",newline="",encoding="utf-8") as stream:
            writer=csv.writer(stream)
            for row_index,row in enumerate(sheet.iter_rows(values_only=True),start=1):
                vals=["" if value is None else str(value) for value in row]
                writer.writerow(vals)
                if any(v.strip() for v in vals):
                    populated+=1
                    if len(sample)<9:
                        sample.append({"excel_row":row_index,
                                       "cells":{str(i+1):v[:350] for i,v in enumerate(vals)
                                                if v.strip()}})
                for v in vals:
                    ids=PRODUCT.findall(v)
                    product_occurrences+=len(ids)
                    products.update(x.upper() for x in ids)
        sheets.append({
            "sheet":sheet.title,
            "declared_rows":sheet.max_row,
            "declared_columns":sheet.max_column,
            "nonempty_rows":populated,
            "csv_filename":dest.name,
            "csv_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
            "original_unique_lroc_ids":len(products),
            "original_id_mentions":product_occurrences,
            "id_preview":sorted(products)[:18],
            "first_nonempty_rows":sample,
        })
    # Preserve the provenance of every source row; reconcile published
    # denominators without silently discarding metadata, blanks or repeats.
    primary=book["WithReliableTemporalPairs"]
    rows=list(primary.iter_rows(values_only=True))
    headers=["" if x is None else str(x) for x in rows[0]]
    before_col=headers.index("Before Image ID")
    after_col=headers.index("After Image ID")
    no_col=headers.index("No.")
    name_col=headers.index("Terrain Name")
    type_col=headers.index("Terrain Type")
    pair_col=headers.index("Temporal Pair")
    valid=[]
    invalid=[]
    targets=set()
    cur_name=None
    cur_type=None
    for excel_row,row in enumerate(rows[1:],start=2):
        serial=row[no_col]
        before="" if row[before_col] is None else str(row[before_col]).strip()
        after="" if row[after_col] is None else str(row[after_col]).strip()
        pair="" if row[pair_col] is None else str(row[pair_col]).strip()
        if row[name_col] is not None:cur_name=str(row[name_col]).strip()
        if row[type_col] is not None:cur_type=str(row[type_col]).strip()
        item={"excel_row":excel_row,"serial":serial,"before":before,
              "after":after,"pair":pair,"terrain_name_fill_down":cur_name,
              "terrain_type_fill_down":cur_type}
        if (PRODUCT.fullmatch(before) and PRODUCT.fullmatch(after)
                and pair.upper()==(before+"_"+after).upper()):
            valid.append(item)
            if cur_name:targets.add((cur_type,cur_name))
        else:
            item["cells"]={str(i+1):str(v)[:160] for i,v in enumerate(row)
                           if v is not None and str(v).strip()}
            invalid.append(item)
    duplicates={}
    for item in valid:
        duplicates[item["pair"]]=duplicates.get(item["pair"],0)+1
    serials=[int(x["serial"]) for x in valid
             if isinstance(x["serial"],(int,float))
             and float(x["serial"]).is_integer()]
    gambart=[x for x in valid
             if "M1138987659LE" in x["pair"].upper()
             or "M1200206882LE" in x["pair"].upper()
             or "GAMBART" in str(x["terrain_name_fill_down"]).upper()]
    pair_audit={
        "header_exact":headers,
        "source_excel_max_row":primary.max_row,
        "source_data_rows":len(rows)-1,
        "exact_pair_id_and_key_reconciled":len(valid),
        "excluded_or_ambiguous_row_count":len(invalid),
        "excluded_or_ambiguous_rows":invalid[:30],
        "pair_duplicate_keys":[{"pair":key,"copies":count} for key,count
                               in sorted(duplicates.items()) if count>1][:50],
        "serial_numeric_row_count":len(serials),
        "serial_min_max":[min(serials),max(serials)] if serials else None,
        "serial_missing_in_1_through_max":sorted(set(range(1,max(serials)+1))-set(serials))
            if serials else [],
        "filled_down_target_name_type_count":len(targets),
        "gambart_or_exact_product_rows":gambart[:35],
        "last_12_excel_rows":[
            {"excel_row":idx,
             "cells":{str(j+1):str(v)[:220] for j,v in enumerate(row)
                      if v is not None and str(v).strip()}}
            for idx,row in list(enumerate(rows,start=1))[-12:]
        ],
        "expected_paper_temporal_pairs":562,
        "expected_paper_targets":74,
        "counts_reconciled_not_coerced":True,
        "note":"pair rows require exact before/after IDs matching temporal pair key; target fill-down is unverified for merged labels",
    }
    # Read primary-source captions and table rows directly from Word OOXML.
    w="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(docx_blob)) as word_package:
        document=ET.fromstring(word_package.read("word/document.xml"))
    paragraphs=[]
    for par in document.iter(w+"p"):
        value="".join(t.text or "" for t in par.iter(w+"t")).strip()
        if value:
            paragraphs.append(value)
    tables=[]
    for tid,tab in enumerate(document.iter(w+"tbl")):
        table_rows=[]
        for tr in tab.findall(w+"tr"):
            cells=[]
            for tc in tr.findall(w+"tc"):
                cell_text=" ".join(
                    "".join(t.text or "" for t in par.iter(w+"t")).strip()
                    for par in tc.iter(w+"p")
                ).strip()
                cells.append(cell_text[:260])
            table_rows.append(cells)
        tables.append({"table_index":tid,"row_count":len(table_rows),
                       "max_columns":max(map(len,table_rows),default=0),
                       "first_4_rows":table_rows[:4],
                       "all_original_rows":table_rows})
    keywords=("562","568","74","41","table s1","table s2","table s3",
              "data s1","fig. s5","figure s5","gambart c","temporal pair")
    matches=[{"paragraph_index":i,"text":p[:750]}
             for i,p in enumerate(paragraphs)
             if any(k in p.lower() for k in keywords)]
    figure_captions=[
        {"paragraph_index":i,"text":p}
        for i,p in enumerate(paragraphs)
        if re.match(r"(?i)^Supplementary\s+Fig\.?\s*S\d+\.",p)
    ]
    docx_audit={
        "original_supplementary_figure_captions":figure_captions,
        "source_docx_filename":docx_names[0],
        "source_docx_sha256":hashlib.sha256(docx_blob).hexdigest(),
        "nonempty_paragraph_count":len(paragraphs),
        "table_count":len(tables),
        "table_structures":tables[:70],
        "relevant_matching_paragraph_count":len(matches),
        "relevant_matching_paragraphs":matches[:100],
        "scientific_scope":"source document structure and captions; no inferred event coordinates",
    }
    out={
        "schema_version":"xiao2025-original-supplement-workbook-audit-v3",
        "original_docx_structure_audit":docx_audit,
        "primary_pair_table_audit":pair_audit,
        "source_zip_sha256":ZIP_SHA,
        "source_workbook":names[0],
        "source_workbook_sha256":hashlib.sha256(xlsx).hexdigest(),
        "sheet_count":len(sheets),
        "sheets":sheets,
        "interpretation":"original workbook structure; expected 562 pairs, 41 events not coerced",
        "scientific_status":"benchmark inventory only; uncalibrated NASA raw pair not recovered"
    }
    Path("diagnostics/isef4_original_xiao_workbook_inventory.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(out,indent=2,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
