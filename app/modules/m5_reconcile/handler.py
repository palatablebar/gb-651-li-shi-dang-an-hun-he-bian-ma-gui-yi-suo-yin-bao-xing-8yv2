from fastapi import APIRouter, Body, Request
from .core import SAMPLE_RECORDS
from .service import execute
router = APIRouter(tags=["M5-索引对账"])

@router.get("/reconcile")
def page(request: Request):
    data = execute(SAMPLE_RECORDS)
    return request.app.state.templates.TemplateResponse(request, "m5_reconcile.html", {"title": "索引对账", "data": data})

@router.post("/api/reconcile")
def api(payload: dict = Body(default={})):
    return execute(payload or None)
