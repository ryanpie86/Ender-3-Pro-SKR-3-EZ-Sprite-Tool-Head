#!/usr/bin/env python3
"""Static checks for config/*.cfg: INI structure, STM32 pin names, Jinja macros.

Klipper itself can't run here (it needs the MCU dictionary), so this catches
the cheap mistakes: a section that doesn't parse, a pin that isn't a port pin
or an EXP alias, a macro whose Jinja doesn't compile.
"""
import configparser
import re
import sys

import jinja2

PIN_RE = re.compile(r"[\^!~]*(P[A-E]\d{1,2}|EXP\d_\d+|probe:z_virtual_endstop|[a-z0-9_]+:(None|gpio\d+))")  # <mcu>:gpioN = a secondary MCU (the Pico)
ok = True
for path in sys.argv[1:]:
    cp = configparser.RawConfigParser(strict=True, inline_comment_prefixes=(";", "#"))
    try:
        cp.read(path)
    except configparser.Error as e:
        print("{}: {}".format(path, e))
        ok = False
        continue
    for s in cp.sections():
        for k, v in cp.items(s):
            if (k.endswith("_pin") or k == "pin" or k == "switch_pin") and not PIN_RE.fullmatch(v.strip()):
                print("{}: [{}] {} = {!r} is not a valid pin".format(path, s, k, v))
                ok = False
            if k == "gcode" or (s.startswith("gcode_macro") and k == "gcode"):
                try:
                    jinja2.Environment().parse(v)
                except jinja2.TemplateSyntaxError as e:
                    print("{}: [{}] gcode template error: {}".format(path, s, e))
                    ok = False
    print("{}: {} sections OK".format(path, len(cp.sections())))
sys.exit(0 if ok else 1)
