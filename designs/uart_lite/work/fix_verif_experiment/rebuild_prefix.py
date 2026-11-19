"""Rebuild the uart_lite verification as generated (before the 2 recorded hand fixes) into an experiment copy."""
import glob
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])           # repository root
dst = Path(sys.argv[2])            # experiment design folder (a copy of designs/uart_lite)

test = (root / "designs/uart_lite/verif/tests/test_uart_lite.py").read_text(encoding="utf-8")
fixed = test[test.index("        # NNC hand fix (G3, triage B): ENV-002"):test.index("        res = start_clock(d)")]
pre_test = test.replace(fixed, "        d.i_rst_n.value = 1\n        self.idle()\n")
log = glob.glob(str(root / "designs/uart_lite/work/logs/agents/A7_tests_r1_*.json"))[0]
gen = json.loads(Path(log).read_text(encoding="utf-8"))["output"]["code"]
print("test file equals the generated A7 output:", pre_test.strip() == gen.strip())

sva = (root / "designs/uart_lite/verif/sva/nnc_chk_rx.sv").read_text(encoding="utf-8")
lines = sva.split("\n")
out = []
skip_comment = False
for ln in lines:
    if "logic mdl_prev;" in ln or "mdl_prev  <= 1'b1;" in ln or "mdl_prev  <= i_rxd;" in ln:
        continue
    if "// NNC hand fix (G3, triage B): a frame starts" in ln:
        skip_comment = True
        continue
    if skip_comment and ln.strip().startswith("//"):
        continue
    skip_comment = False
    out.append(ln.replace("if (mdl_prev && !i_rxd) begin", "if (!i_rxd) begin"))
pre_sva = "\n".join(out)
log = glob.glob(str(root / "designs/uart_lite/work/logs/agents/A5_sva_rx_r0_*.json"))[0]
body = json.loads(Path(log).read_text(encoding="utf-8"))["output"]["body"]
print("checker contains the generated A5 body:", body.strip() in pre_sva)

(dst / "verif/tests/test_uart_lite.py").write_text(pre_test, encoding="utf-8", newline="\n")
(dst / "verif/sva/nnc_chk_rx.sv").write_text(pre_sva, encoding="utf-8", newline="\n")
print("written to", dst)
