#!/usr/bin/env python3
"""Run a Fusion script's run() against the stub adsk package and report.

    python3 run_mock.py                # HarnessMast (default): the folder under Fusion/ whose .py has the same name
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = sys.argv[1] if len(sys.argv) > 1 else "HarnessMast"
sys.path.insert(0, os.path.join(HERE, "mock_adsk"))
sys.path.insert(0, os.path.join(HERE, "..", NAME))

import adsk.core  # noqa: E402  (the stub)
S = importlib.import_module(NAME)

assert S.HAVE_ADSK, "script did not pick up the stub adsk package"
S.run(None)
msg = adsk.core.MESSAGES[-1]
if msg.startswith("Failed"):
    print(msg)
    sys.exit(1)
comp = adsk.core.Application.get().activeProduct.rootComponent
print("features total:", len(adsk.core.LOG))
for b in comp.bodies:
    ops = {}
    for _, op, _ in b.features:
        ops[op] = ops.get(op, 0) + 1
    print("  {}: {} features {}".format(b.name, len(b.features), ops))
print("planes:", [(p.name or "(temp)", p.axis, round(p.value * 10, 2), "deleted" if p.deleted else "") for p in comp.constructionPlanes.items])
print("message box:\n" + msg)
