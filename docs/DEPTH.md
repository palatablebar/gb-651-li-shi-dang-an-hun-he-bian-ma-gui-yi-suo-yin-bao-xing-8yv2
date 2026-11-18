# 深度登记 历史档案混合编码归一与索引保形

        - 规模：中型
        - 核心规则：候选解码必须完整且无替换字符；档号、盒号与超大流水号始终按字符串逐字保留。
        - 使用者与工作流：导入随仓样例，逐模块复核，最后导出单一证据清单。

        ## 功能模块

        | 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
        |---|---|---|---|---|
        | M1 文件采信 | 运行样例并复核证据 | `/api/intake/run` / `/intake` | `app/modules/m1_intake/core.py` `app/modules/m1_intake/service.py` | `tests/test_m1_intake.py` |
| M2 编码判定 | 运行样例并复核证据 | `/api/encoding/detect` / `/encoding` | `app/modules/m2_encoding/core.py` `app/modules/m2_encoding/service.py` | `tests/test_m2_encoding.py` |
| M3 字段保形 | 运行样例并复核证据 | `/api/fields/normalize` / `/fields` | `app/modules/m3_fields/core.py` `app/modules/m3_fields/service.py` | `tests/test_m3_fields.py` |
| M4 内容归一 | 运行样例并复核证据 | `/api/content/normalize` / `/content` | `app/modules/m4_content/core.py` `app/modules/m4_content/service.py` | `tests/test_m4_content.py` |
| M5 索引对账 | 运行样例并复核证据 | `/api/reconcile` / `/reconcile` | `app/modules/m5_reconcile/core.py` `app/modules/m5_reconcile/service.py` | `tests/test_m5_reconcile.py` |
| M6 批次导出 | 运行样例并复核证据 | `/api/export/evidence.csv` / `/runs` | `app/modules/m6_runs/core.py` `app/modules/m6_runs/service.py` | `tests/test_m6_runs.py` |

        ## 陷阱登记

        | TRAP | 现象 | 朴素实现 | 本项目处理 | 处理位置 | 测试 |
        |---|---|---|---|---|---|
        | TRAP-01 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m1_intake/core.py` | `tests/test_m1_intake.py::test_trap_1` |
| TRAP-02 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m2_encoding/core.py` | `tests/test_m2_encoding.py::test_trap_1` |
| TRAP-03 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m3_fields/core.py` | `tests/test_m3_fields.py::test_trap_1` |
| TRAP-04 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m4_content/core.py` | `tests/test_m4_content.py::test_trap_1` |
| TRAP-05 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m5_reconcile/core.py` | `tests/test_m5_reconcile.py::test_trap_1` |
| TRAP-07 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m6_runs/core.py` | `tests/test_m6_runs.py::test_trap_1` |
| TRAP-08 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m1_intake/core.py` | `tests/test_m1_intake.py::test_trap_2` |
| TRAP-09 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m2_encoding/core.py` | `tests/test_m2_encoding.py::test_trap_2` |
| TRAP-16 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m3_fields/core.py` | `tests/test_m3_fields.py::test_trap_2` |
| TRAP-18 | 真实边界输入 | 朴素处理会错分 | 保留证据并稳定裁决 | `app/modules/m4_content/core.py` | `tests/test_m4_content.py::test_trap_2` |
| TRAP-21 | 同档号分装多盒且归一记录缺盒号 | 朴素实现随机认领一盒，认错原件 | 不猜测，记 AMBIGUOUS_BOX 存疑，保留候选盒号与原行依据，补件后重对账 | `app/modules/m5_reconcile/core.py` | `tests/test_m5_reconcile.py::test_ambiguous_box_not_guessed` |
| TRAP-22 | 盒号前导零 | 数值化使 "07" 与 "7" 混同 | 档号盒号全程字符串逐字比较 | `app/modules/m5_reconcile/core.py` | `tests/test_m5_reconcile.py::test_leading_zero_box_distinct` |
| TRAP-23 | 同一批次重复导出 | 每次导出都新增凭据 | 内容摘要去重复用 run_id，已交接凭据可按 run_id 原样取回 | `app/modules/m6_runs/core.py` `app/store.py` | `tests/test_m6_runs.py::test_rerun_same_batch_no_new_voucher` |

        ## 对账规则

        - 输入记录数 = 有效记录数 + 隔离记录数 + 空记录数。
        - 记录级守恒：归一记录数 = 已核对 + 存疑 + 多出；索引原件（档号，盒号）数 = 已核对 + 冲突 + 缺失。
        - 凭据上的已核对记录必须指向唯一（档号，盒号）；缺盒号且同档号多盒的记录不猜测，记为存疑并保留原行依据。
        - 批次凭据按内容摘要去重；补件后重新对账生成新凭据，已交接凭据可原样取回。
        - 核心数值或事件数在转换、判定和导出之间保持守恒。
        - 同一输入摘要重跑复用原运行编号，不增加结果行。

        ## 已知不覆盖

        - 生产系统连接、身份认证和外部密钥不在演示范围内。
