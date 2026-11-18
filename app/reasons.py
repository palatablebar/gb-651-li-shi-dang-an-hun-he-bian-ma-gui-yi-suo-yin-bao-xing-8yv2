REASONS = {
    "BAD_COLUMNS": "字段数量不符", "EMPTY_VALUE": "必要值为空",
    "DUPLICATE_CONFLICT": "同一业务键取值冲突", "TRUNCATED": "尾记录不完整",
    "INVALID_VALUE": "值不符合定义", "STALE_VERSION": "提交版本已过期",
    "AMBIGUOUS_BOX": "同档号分装多盒且缺盒号，无法唯一指向原件",
    "ORPHAN_RECORD": "归一记录在索引中无对应原件",
    "MISSING_RECORD": "索引原件在归一结果中缺失",
}

def reason(code: str) -> str:
    return REASONS.get(code, "未登记原因")
