from app.modules.m5_reconcile.core import reconcile_records
from app.modules.m6_runs.core import SAMPLE, csv_text, rows_from_reconcile, run
class FakeStore:
    def __init__(self): self.values={}
    def record(self,digest,rid,result): self.values.setdefault(digest,(rid,result)); return {"run_id":self.values[digest][0],"result":self.values[digest][1]}
def test_csv_header(): assert csv_text(SAMPLE["rows"]).startswith("source_line,archive_id,reason")
def test_csv_preserves_zero(): assert "000123" in csv_text(SAMPLE["rows"])
def test_run_id_stable(): assert run({})["run_id"]==run({})["run_id"]
def test_digest_stable(): assert run({})["digest"]==run({})["digest"]
def test_trap_1(): # TRAP-07
    store=FakeStore(); assert run({"store":store})["run_id"]==run({"store":store})["run_id"]
def test_trap_2():
    assert run({"rows":SAMPLE["rows"]})["input_count"]==2
def test_counts_quarantine(): assert run({})["quarantine_count"]==1
def test_counts_valid(): assert run({})["valid_count"]==1

TWO_BOX_INDEX=[{"archive_id":"000123","box_id":"07"},{"archive_id":"000123","box_id":"08"}]
def doubtful_recon():
    return reconcile_records(TWO_BOX_INDEX,[
        {"source_line":2,"archive_id":"000123","box_id":"","raw":{"档号":"000123","盒号":""}},
        {"source_line":3,"archive_id":"000123","box_id":"07"}])
def supplemented_recon():
    return reconcile_records(TWO_BOX_INDEX,[
        {"source_line":2,"archive_id":"000123","box_id":"08"},
        {"source_line":3,"archive_id":"000123","box_id":"07"}])

def test_csv_columns_follow_row_fields():
    rows=[{"source_line":2,"archive_id":"000123","box_id":"07","status":"matched","reason":"OK"}]
    assert csv_text(rows).splitlines()[0]=="source_line,archive_id,box_id,status,reason"
def test_voucher_verified_points_to_unique_original():
    out=run({"reconcile":doubtful_recon()})
    assert out["valid_count"]==1 and out["doubtful_count"]==1
    assert "matched" in out["csv"] and "AMBIGUOUS_BOX" in out["csv"]
def test_voucher_csv_keeps_leading_zeros():
    csv=run({"reconcile":doubtful_recon()})["csv"]
    assert "000123" in csv and ",07," in csv
def test_voucher_keeps_doubtful_raw_evidence():
    out=run({"reconcile":doubtful_recon()})
    assert "档号" in out["csv"]
    assert out["missing_count"]==1
    assert out["missing"]==[{"archive_id":"000123","box_id":"08"}]
def test_rerun_same_batch_no_new_voucher(): # TRAP-23
    store=FakeStore()
    first=run({"reconcile":doubtful_recon(),"store":store})
    second=run({"reconcile":doubtful_recon(),"store":store})
    assert first["run_id"]==second["run_id"]
    assert len(store.values)==1
def test_supplement_yields_new_voucher_and_old_kept():
    store=FakeStore()
    before=run({"reconcile":doubtful_recon(),"store":store})
    after=run({"reconcile":supplemented_recon(),"store":store})
    assert before["run_id"]!=after["run_id"]
    assert len(store.values)==2
    assert after["valid_count"]==2 and after["doubtful_count"]==0
    assert store.values[before["digest"]][1]["csv"]==before["csv"]
def test_rows_from_reconcile_sorted_by_line():
    rows=rows_from_reconcile(doubtful_recon())
    assert [r["source_line"] for r in rows]==[2,3]
def test_inferred_box_marked_on_voucher():
    recon=reconcile_records([{"archive_id":"000123","box_id":"07"}],[{"source_line":2,"archive_id":"000123","box_id":""}])
    out=run({"reconcile":recon})
    assert out["valid_count"]==1
    assert "box_inferred" in out["csv"].splitlines()[0]
