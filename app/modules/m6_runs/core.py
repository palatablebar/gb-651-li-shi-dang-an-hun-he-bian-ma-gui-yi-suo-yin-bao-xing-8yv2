import csv, io, json
from app.manifest import canonical_digest, run_id
SAMPLE={"store":None,"rows":[{"source_line":2,"archive_id":"000123","reason":"OK"},{"source_line":5,"archive_id":"BAD","reason":"BAD_COLUMNS"}]}
COLUMNS=["source_line","archive_id","box_id","status","reason","candidates","box_inferred","raw"]
def _cell(value):
    if value is None: return ""
    if isinstance(value,bool): return "true" if value else "false"
    if isinstance(value,(dict,list)): return json.dumps(value,ensure_ascii=False,sort_keys=True)
    return str(value)
def _columns(rows):
    seen=set()
    for row in rows: seen.update(row)
    ordered=[name for name in COLUMNS if name in seen]
    return ordered+sorted(name for name in seen if name not in COLUMNS)
def csv_text(rows):
    cols=_columns(rows) or COLUMNS[:5]
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=cols,lineterminator="\n"); writer.writeheader()
    for row in rows: writer.writerow({name:_cell(row.get(name)) for name in cols})
    return out.getvalue()
def rows_from_reconcile(recon):
    rows=[]
    for item in recon.get("matched",[]):
        row={"source_line":item.get("source_line"),"archive_id":item.get("archive_id"),"box_id":item.get("box_id"),"status":"matched","reason":"OK"}
        if item.get("box_inferred"): row["box_inferred"]=True
        rows.append(row)
    for item in recon.get("doubtful",[]):
        row={"source_line":item.get("source_line"),"archive_id":item.get("archive_id"),"box_id":item.get("box_id"),"status":"doubtful","reason":item.get("reason","")}
        if item.get("candidates"): row["candidates"]=item["candidates"]
        if item.get("raw") is not None: row["raw"]=item["raw"]
        rows.append(row)
    for item in recon.get("orphan",[]):
        row={"source_line":item.get("source_line"),"archive_id":item.get("archive_id"),"box_id":item.get("box_id"),"status":"orphan","reason":"ORPHAN_RECORD"}
        if item.get("raw") is not None: row["raw"]=item["raw"]
        rows.append(row)
    rows.sort(key=lambda row:(row.get("source_line") is None,row.get("source_line") or 0))
    return rows
def _verified(row):
    if "status" in row: return row["status"]=="matched"
    return row.get("reason")=="OK"
def run(payload):
    store=payload.get("store"); recon=payload.get("reconcile")
    if recon is not None:
        rows=rows_from_reconcile(recon)
        missing=sorted((dict(m) for m in recon.get("missing",[])),key=lambda m:(str(m.get("archive_id")),str(m.get("box_id"))))
    else:
        rows=[dict(r) for r in payload.get("rows",SAMPLE["rows"])]
        missing=[]
    basis={"rows":rows,"missing":missing}
    digest=canonical_digest(basis); rid=run_id(basis)
    valid=sum(1 for row in rows if _verified(row))
    voucher={
        "run_id":rid,"digest":digest,"csv":csv_text(rows),
        "input_count":len(rows),"valid_count":valid,"quarantine_count":len(rows)-valid,
        "doubtful_count":sum(1 for row in rows if row.get("status")=="doubtful"),
        "orphan_count":sum(1 for row in rows if row.get("status")=="orphan"),
        "missing_count":len(missing),"missing":missing,
        "reason":"OK" if valid==len(rows) and not missing else "DIFF",
    }
    if store: voucher["run_id"]=store.record(digest,rid,voucher)["run_id"]
    return {"status":"READY",**voucher}
