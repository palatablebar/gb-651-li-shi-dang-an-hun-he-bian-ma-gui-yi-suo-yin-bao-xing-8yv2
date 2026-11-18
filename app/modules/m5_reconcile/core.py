SAMPLE={"index_ids":["000123","9007199254740993","000404"],"normalized_ids":["000123","9007199254740993","000777"],"quarantine":1,"empty":0}
SAMPLE_RECORDS={
    "index_records":[
        {"archive_id":"000123","box_id":"07"},
        {"archive_id":"000123","box_id":"08"},
        {"archive_id":"9007199254740993","box_id":"08"},
    ],
    "normalized_records":[
        {"source_line":2,"archive_id":"000123","box_id":"","raw":{"档号":"000123","盒号":"","题名":"年度 汇编"}},
        {"source_line":3,"archive_id":"9007199254740993","box_id":"08","raw":{"档号":"9007199254740993","盒号":"08","题名":"会议"}},
        {"source_line":4,"archive_id":"000404","box_id":"02","raw":{"档号":"000404","盒号":"02","题名":"补遗"}},
    ],
    "quarantine":1,
    "empty":0,
}
def reconcile(index_ids, normalized_ids, quarantine=0, empty=0):
    left=set(map(str,index_ids)); right=set(map(str,normalized_ids)); missing=sorted(left-right); orphan=sorted(right-left)
    return {"index_count":len(index_ids),"output_count":len(normalized_ids),"missing":missing,"orphan":orphan,"quarantine_count":quarantine,"empty_count":empty,"balanced":len(normalized_ids)+quarantine+empty>=len(right)}
def _text(value):
    if value is None: return ""
    return str(value).strip()
def reconcile_records(index_records, normalized_records, quarantine=0, empty=0):
    pair_counts={}
    for entry in index_records:
        pair=(_text(entry.get("archive_id")),_text(entry.get("box_id")))
        pair_counts[pair]=pair_counts.get(pair,0)+1
    duplicate_pairs={pair for pair,count in pair_counts.items() if count>1}
    index_duplicates=[{"archive_id":a,"box_id":b,"count":pair_counts[(a,b)]} for (a,b) in sorted(duplicate_pairs)]
    boxes_by_archive={}
    for archive_id,box_id in pair_counts: boxes_by_archive.setdefault(archive_id,set()).add(box_id)
    states=[]; claims={}
    for rec in normalized_records:
        archive_id=_text(rec.get("archive_id")); box_id=_text(rec.get("box_id"))
        row={"source_line":rec.get("source_line"),"archive_id":archive_id,"box_id":box_id}
        if rec.get("raw") is not None: row["raw"]=rec.get("raw")
        st={"row":row,"pair":None,"inferred":False}
        if not archive_id:
            st["kind"]="doubtful"; row["reason"]="EMPTY_VALUE"
        elif not box_id:
            boxes=sorted(boxes_by_archive.get(archive_id,()))
            if len(boxes)>1:
                st["kind"]="doubtful"; row["reason"]="AMBIGUOUS_BOX"; row["candidates"]=boxes
            elif boxes:
                st["kind"]="claim"; st["pair"]=(archive_id,boxes[0]); st["inferred"]=True
            else:
                st["kind"]="orphan"
        else:
            pair=(archive_id,box_id)
            if pair in pair_counts: st["kind"]="claim"; st["pair"]=pair
            else: st["kind"]="orphan"
        if st["kind"]=="claim": claims.setdefault(st["pair"],[]).append(len(states))
        states.append(st)
    conflict_pairs=set()
    for pair,owners in claims.items():
        if len(owners)>1 or pair in duplicate_pairs:
            conflict_pairs.add(pair)
            for i in owners:
                states[i]["kind"]="doubtful"; states[i]["row"]["reason"]="DUPLICATE_CONFLICT"
        else:
            i=owners[0]; states[i]["kind"]="matched"
            states[i]["row"]["archive_id"],states[i]["row"]["box_id"]=pair
            if states[i]["inferred"]: states[i]["row"]["box_inferred"]=True
    matched=[st["row"] for st in states if st["kind"]=="matched"]
    doubtful=[st["row"] for st in states if st["kind"]=="doubtful"]
    orphan=[st["row"] for st in states if st["kind"]=="orphan"]
    missing=[{"archive_id":a,"box_id":b} for (a,b) in sorted(pair_counts) if (a,b) not in claims]
    matched_pairs=len(claims)-len(conflict_pairs)
    return {
        "input_count":len(states),"index_count":len(index_records),
        "matched_count":len(matched),"doubtful_count":len(doubtful),
        "orphan_count":len(orphan),"missing_count":len(missing),"conflict_count":len(conflict_pairs),
        "quarantine_count":quarantine,"empty_count":empty,
        "matched":matched,"doubtful":doubtful,"orphan":orphan,"missing":missing,
        "index_duplicates":index_duplicates,
        "balanced":len(states)==len(matched)+len(doubtful)+len(orphan) and len(pair_counts)==matched_pairs+len(conflict_pairs)+len(missing),
    }
def run(payload):
    data=SAMPLE|payload
    if "index_records" in data or "normalized_records" in data:
        out=reconcile_records(data.get("index_records") or [],data.get("normalized_records") or [],data.get("quarantine",0),data.get("empty",0))
        return {"status":"READY",**out,"reason":"AMBIGUOUS" if out["doubtful"] else ("DIFF" if out["missing"] or out["orphan"] else "OK")}
    out=reconcile(data["index_ids"],data["normalized_ids"],data.get("quarantine",0),data.get("empty",0))
    return {"status":"READY","input_count":out["index_count"],"valid_count":out["output_count"],**out,"reason":"DIFF" if out["missing"] or out["orphan"] else "OK"}
