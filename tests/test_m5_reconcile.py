from app.modules.m5_reconcile.core import SAMPLE_RECORDS, reconcile, reconcile_records, run
def test_trap_1(): # TRAP-05
    assert reconcile(["001"],["001"])["missing"]==[]
def test_trap_2(): assert reconcile(["A"],["B"])["orphan"]==["B"]
def test_missing_sorted(): assert reconcile(["B","A"],[])["missing"]==["A","B"]
def test_duplicates_counted_as_input(): assert reconcile(["A","A"],["A"])["index_count"]==2
def test_large_id_preserved(): assert reconcile(["9007199254740993"],["9007199254740993"])["missing"]==[]
def test_quarantine_in_balance(): assert reconcile(["A"],[],1)["balanced"] is True
def test_sample_has_two_sides(): assert run({})["reason"]=="DIFF"
def test_clean_is_ok(): assert run({"index_ids":["A"],"normalized_ids":["A"],"quarantine":0,"empty":0})["reason"]=="OK"

INDEX=[{"archive_id":"000123","box_id":"07"},{"archive_id":"000123","box_id":"08"},{"archive_id":"9007199254740993","box_id":"08"}]

def test_ambiguous_box_not_guessed(): # TRAP-21
    out=reconcile_records(INDEX,[{"source_line":2,"archive_id":"000123","box_id":""}])
    assert out["matched"]==[]
    assert out["doubtful"][0]["reason"]=="AMBIGUOUS_BOX"
    assert out["doubtful"][0]["candidates"]==["07","08"]
    assert out["doubtful_count"]==1
def test_ambiguous_keeps_line_evidence():
    raw={"档号":"000123","盒号":""}
    out=reconcile_records(INDEX,[{"source_line":2,"archive_id":"000123","box_id":"","raw":raw}])
    assert out["doubtful"][0]["source_line"]==2
    assert out["doubtful"][0]["raw"]==raw
def test_single_box_inferred():
    out=reconcile_records(INDEX,[{"source_line":3,"archive_id":"9007199254740993","box_id":""}])
    assert out["matched"][0]["box_id"]=="08"
    assert out["matched"][0]["box_inferred"] is True
def test_leading_zero_box_distinct(): # TRAP-22
    out=reconcile_records([{"archive_id":"000123","box_id":"07"}],[{"source_line":2,"archive_id":"000123","box_id":"7"}])
    assert out["matched"]==[] and out["orphan"][0]["box_id"]=="7"
    assert out["missing"]==[{"archive_id":"000123","box_id":"07"}]
def test_leading_zero_preserved_in_match():
    out=reconcile_records([{"archive_id":"000123","box_id":"07"}],[{"source_line":2,"archive_id":"000123","box_id":"07"}])
    assert out["matched"][0]["archive_id"]=="000123"
    assert out["matched"][0]["box_id"]=="07"
def test_duplicate_claims_both_doubtful():
    recs=[{"source_line":2,"archive_id":"9007199254740993","box_id":"08"},{"source_line":3,"archive_id":"9007199254740993","box_id":"08"}]
    out=reconcile_records(INDEX,recs)
    assert out["matched"]==[]
    assert [d["reason"] for d in out["doubtful"]]==["DUPLICATE_CONFLICT","DUPLICATE_CONFLICT"]
def test_orphan_record():
    out=reconcile_records(INDEX,[{"source_line":4,"archive_id":"000777","box_id":"01"}])
    assert out["orphan"][0]["archive_id"]=="000777"
def test_missing_pairs_listed():
    out=reconcile_records(INDEX,[])
    assert out["missing"]==[{"archive_id":"000123","box_id":"07"},{"archive_id":"000123","box_id":"08"},{"archive_id":"9007199254740993","box_id":"08"}]
def test_missing_archive_id_doubtful():
    out=reconcile_records(INDEX,[{"source_line":5,"archive_id":"","box_id":"07"}])
    assert out["doubtful"][0]["reason"]=="EMPTY_VALUE"
def test_supplement_clears_doubt():
    before=reconcile_records(INDEX,[{"source_line":2,"archive_id":"000123","box_id":""}])
    after=reconcile_records(INDEX,[{"source_line":2,"archive_id":"000123","box_id":"07"}])
    assert before["doubtful_count"]==1
    assert after["matched_count"]==1 and after["doubtful_count"]==0
    assert after["missing"]==[{"archive_id":"000123","box_id":"08"},{"archive_id":"9007199254740993","box_id":"08"}]
def test_balance_conservation():
    out=reconcile_records(INDEX,[{"source_line":2,"archive_id":"000123","box_id":""},{"source_line":3,"archive_id":"9007199254740993","box_id":"08"}])
    assert out["input_count"]==out["matched_count"]+out["doubtful_count"]+out["orphan_count"]
    assert out["balanced"] is True
def test_sample_records_ambiguous():
    out=run({"index_records":SAMPLE_RECORDS["index_records"],"normalized_records":SAMPLE_RECORDS["normalized_records"]})
    assert out["reason"]=="AMBIGUOUS"
    assert out["matched_count"]==1 and out["doubtful_count"]==1 and out["orphan_count"]==1
