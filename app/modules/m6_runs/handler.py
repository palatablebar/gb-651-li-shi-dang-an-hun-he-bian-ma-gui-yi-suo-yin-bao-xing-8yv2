from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import Response
from .service import execute
router = APIRouter(tags=["M6-批次导出"])

@router.get("/runs")
def page(request: Request):
    data = execute({"store": request.app.state.store})
    return request.app.state.templates.TemplateResponse(request, "m6_runs.html", {"title": "批次导出", "data": data})

@router.get("/api/runs")
def runs(request: Request):
    execute({"store": request.app.state.store})
    return {"runs": request.app.state.store.all()}

@router.get("/api/runs/{run_id}")
def run_detail(run_id: str, request: Request):
    found = request.app.state.store.get(run_id)
    if found is None:
        raise HTTPException(status_code=404, detail="批次不存在")
    return found

@router.get("/api/export/evidence.csv")
def export(request: Request):
    data = execute({"store": request.app.state.store})
    return Response(data["csv"], media_type="text/csv", headers={"Content-Disposition": "attachment; filename=evidence.csv"})

@router.post("/api/export/evidence.csv")
def export_batch(request: Request, payload: dict = Body(default={})):
    return execute({**(payload or {}), "store": request.app.state.store})
