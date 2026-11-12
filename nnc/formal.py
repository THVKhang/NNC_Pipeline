"""Formal check of the generated assertions with SymbiYosys (stage `formal`, code only, no LLM).

Simulation shows that no assertion failed for the stimulus that ran. A formal tool searches every
input sequence: bounded model checking (BMC) finds a counterexample of up to `depth` clock cycles, and
k-induction proves the assertion for every cycle. The open-source Yosys frontends accept immediate
assertions inside `always` blocks but not clocked concurrent SVA, so this module TRANSLATES the small
SVA subset the checker generator emits into an equivalent immediate form, by code:

    @(posedge CLK) [disable iff (D)]  S1 (|-> | |=>) S2        S := e0 ##n1 e1 ##n2 e2 ...
    @(posedge CLK) [disable iff (D)]  e                         (invariant)

A shift register follows each attempt: the antecedent elements gate it, each consequent element is an
`assert` at its cycle, and D clears every attempt in flight (disable iff). `$past`, `$stable`, `$rose`,
`$fell` are kept (Yosys supports them in clocked blocks); `$isunknown(x)` becomes 0 (no X in formal).
Anything else (ranges `##[a:b]`, repetition, `throughout`, `until`, ...) is reported as UNSUPPORTED,
never approximated. Each check is proved alone (`ifdef NNC_FV_<id>`), so one failure does not hide
another.

Environment. The ports of the DUT are free inputs except the resets, which are asserted in the first
cycles (code). An input protocol (for example "PENABLE only after a PSEL setup cycle") is an
assumption about the environment: a counterexample that breaks one is not a design bug. Assumptions
are written in `verif/formal/nnc_env.sv` (by the designer or agent A13, from the specification only)
and listed in the report; without them a counterexample is reported as such, for review.

Clocks: synchronous designs are modelled with one global clock (`multiclock off`); designs with
clock_relation=async with `multiclock on` (every clock a free input, so every ratio and phase).
Results per assertion: PROVEN (k-induction), BOUNDED (no counterexample within `depth` cycles,
induction inconclusive), CEX (counterexample trace), UNSUPPORTED, ERROR.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from nnc.contract import is_async
from nnc.sim import checker_files, rtl_files, tb_top
from nnc.simhost import SimHost

DEFAULT_DEPTH = 20
DEFAULT_TIMEOUT_S = 600          # per SymbiYosys task (bmc, prove, cover) of one check
_UNSUPPORTED = re.compile(r"##\s*\[|\[\s*\*|\[\s*->|\[\s*=|\b(throughout|within|intersect|s_eventually|eventually|"
                          r"until|until_with|s_until|first_match|strong|weak|nexttime|always|accept_on|reject_on|"
                          r"sync_accept_on|sync_reject_on|not|implies|iff|case|if)\b|\$(sampled|global_clock|future_gclk)")
_ASSERT = re.compile(r"\b(?:a_((CHK_\d{3})\w*)\s*:\s*)?assert\s+property\s*\(")


class FormalError(ValueError):
    pass


_NONSYNTH = [(re.compile(r"\btime\b|\$(?:time|realtime|stime)\b"), "simulation time"),
             (re.compile(r"\[\s*\$\s*\]|\.(?:push_back|push_front|pop_back|pop_front)\b"), "queues"),
             (re.compile(r"\bvoid\s*'"), "void casts"),
             (re.compile(r"\b(?:class|new|string|real|shortreal|realtime|chandle|mailbox|semaphore)\b"),
              "non-synthesizable types"),
             (re.compile(r"\$(?:urandom|random|urandom_range)\b"), "random functions"),
             (re.compile(r"#\s*\d"), "delays"),
             (re.compile(r"\balways\s*@\s*\((?![^)]*\b(?:posedge|negedge)\b)(?!\s*\*)"), "event-triggered blocks")]


def nonsynth(text: str) -> str | None:
    """Why a checker module cannot be read by a formal tool (simulation-only constructs), or None."""
    code = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", text, flags=re.S))
    code = re.sub(r'"[^"\n]*"', '""', code)
    for rx, why in _NONSYNTH:
        m = rx.search(code)
        if m:
            return f"{why} (`{m.group(0).strip()}`)"
    return None


@dataclass
class Prop:
    check: str                  # CHK-001
    clock: str = ""
    disable: str | None = None
    ante: list[tuple[int, str]] = field(default_factory=list)    # (delay before, expr)
    cons: list[tuple[int, str]] = field(default_factory=list)
    overlap: bool = True        # |-> (True) or |=> (False); ante empty: invariant
    span: tuple[int, int] = (0, 0)   # character span of the whole statement in the source
    unsupported: str = ""
    label: str = ""             # CHK_001 or CHK_001_rd: one check may have several assertions


def _match_paren(s: str, i: int) -> int:
    """Index of the parenthesis closing s[i] == '('."""
    depth = 0
    for k in range(i, len(s)):
        depth += s[k] == "("
        depth -= s[k] == ")"
        if depth == 0:
            return k
    raise FormalError("unbalanced parentheses")


def _split_top(s: str, seps: tuple[str, ...]) -> list[str]:
    """Split s at separators outside (), [], {}; separators are kept as separate items."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(s):
        c = s[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if depth == 0:
            hit = next((x for x in seps if s.startswith(x, i)), None)
            if hit:
                out += [cur, hit]
                cur, i = "", i + len(hit)
                continue
        cur += c
        i += 1
    return out + [cur]


def _sequence(text: str) -> list[tuple[int, str]]:
    """'a ##1 b ##2 c' -> [(0, a), (1, b), (2, c)]."""
    parts = re.split(r"##\s*(\d+)", text)
    seq = [(0, parts[0].strip())]
    for k in range(1, len(parts), 2):
        seq.append((int(parts[k]), parts[k + 1].strip()))
    for d, e in seq:
        if not e:
            raise FormalError("empty sequence element")
    return seq


_ISUNKNOWN = re.compile(r"\$isunknown\s*\([^()]*(?:\([^()]*\)[^()]*)*\)")


def _expr(e: str) -> str:
    e = _ISUNKNOWN.sub("1'b0", e)
    e = e.strip()
    while e.startswith("(") and _match_paren(e, 0) == len(e) - 1:
        e = e[1:-1].strip()
    return e


def parse_property(check: str, body: str) -> Prop:
    """Parse the text inside `assert property ( ... )`."""
    s = body.strip()
    m = re.match(r"@\s*\(\s*posedge\s+([A-Za-z_]\w*)\s*\)", s)
    if not m:
        return Prop(check, "", None, unsupported="no single `@(posedge clk)` clocking")
    clock, s = m.group(1), s[m.end():].strip()
    disable = None
    m = re.match(r"disable\s+iff\s*\(", s)
    if m:
        end = _match_paren(s, m.end() - 1)
        disable, s = s[m.end():end].strip(), s[end + 1:].strip()
    hit = _UNSUPPORTED.search(s)
    if hit:
        return Prop(check, clock, disable, unsupported=f"SVA construct `{hit.group(0)}`")
    while s.startswith("(") and _match_paren(s, 0) == len(s) - 1:     # ((A |-> B)) -> A |-> B
        s = s[1:-1].strip()
    parts = _split_top(s, ("|->", "|=>"))
    p = Prop(check, clock, disable)
    try:
        if len(parts) == 1:
            p.cons = [(d, _expr(e)) for d, e in _sequence(s)]
        elif len(parts) == 3:
            p.ante = [(d, _expr(e)) for d, e in _sequence(_expr(parts[0]))]
            p.cons = [(d, _expr(e)) for d, e in _sequence(_expr(parts[2]))]
            p.overlap = parts[1] == "|->"
        else:
            p.unsupported = "more than one implication"
    except FormalError as e:
        p.unsupported = str(e)
    if not p.unsupported and any("##" in e for _, e in p.ante + p.cons):
        p.unsupported = "a delay inside parentheses (nested sequence)"
    return p


def find_properties(text: str) -> list[Prop]:
    """Every `a_CHK_xxx: assert property (...)` statement with its action block, in source order."""
    out = []
    for m in _ASSERT.finditer(text):
        if not m.group(2):
            continue
        start = m.end() - 1
        end = _match_paren(text, start)
        tail = re.match(r"\s*else\s+begin\b.*?\bend\b", text[end + 1:], re.S)
        stop = end + 1 + (tail.end() if tail else 0)
        if not tail and text[stop:stop + 1] == ";":
            stop += 1
        p = parse_property(m.group(2).replace("_", "-"), text[start + 1:end])
        p.label = m.group(1)
        p.span = (m.start(), stop)
        out.append(p)
    return out


def translate(p: Prop) -> str:
    """Immediate-assertion form of one property, enabled by `ifdef NNC_FV_<CHK_xxx>`."""
    tag = p.label or p.check.replace("-", "_")
    chk = p.check.replace("-", "_")
    if p.unsupported:
        return f"  // {p.check} (a_{tag}): not translated for formal ({p.unsupported})\n"
    # elements in order with absolute offsets; consequent starts at the end of the antecedent (+1 for |=>)
    elems, t = [], 0
    for i, (d, e) in enumerate(p.ante):
        t += d if i else 0
        elems.append((t, "a", e))
    base = t + (0 if (p.overlap or not p.ante) else 1)
    t = base
    for i, (d, e) in enumerate(p.cons):
        t += d if i else 0
        elems.append((t, "c", e))
    last = max(o for o, _, _ in elems)
    last_ante = len(p.ante) - 1          # index in elems of the last antecedent element (-1: none)
    en = f"!({p.disable})" if p.disable else "1'b1"
    lines = [f"`ifdef NNC_FV_{chk}", f"  // {p.check}: assertion a_{tag} in immediate form for formal (nnc/formal.py)"]
    if last:
        lines.append(f"  reg [{last}:1] nnc_fv_s_{tag} = '0;")
    lines += [f"  reg nnc_fv_ok_{tag}_{k};" for k in range(last + 1)]
    lines.append(f"  always @(posedge {p.clock}) begin")
    for k in range(last + 1):
        prev = "1'b1" if k == 0 else f"nnc_fv_s_{tag}[{k}]"
        lines.append(f"    nnc_fv_ok_{tag}_{k} = {en} && {prev};")
        if k == 0 and last_ante < 0:     # invariant: vacuity = the check is enabled at all
            lines.append(f"    cover (nnc_fv_ok_{tag}_0);")
        for i, (o, kind, e) in enumerate(elems):
            if o != k:
                continue
            if kind == "a":
                lines.append(f"    nnc_fv_ok_{tag}_{k} = nnc_fv_ok_{tag}_{k} && ({e});")
                if i == last_ante:       # vacuity: the antecedent can match under the assumptions
                    lines.append(f"    cover (nnc_fv_ok_{tag}_{k});")
            else:
                lines.append(f"    if (nnc_fv_ok_{tag}_{k}) assert ({e});")
                lines.append(f"    nnc_fv_ok_{tag}_{k} = nnc_fv_ok_{tag}_{k} && ({e});")
        if k < last:
            lines.append(f"    nnc_fv_s_{tag}[{k + 1}] <= nnc_fv_ok_{tag}_{k};")
    lines += ["  end", "`endif"]
    return "\n".join(lines) + "\n"


def formal_view(text: str) -> tuple[str, list[Prop]]:
    """Checker source for formal: each concurrent assertion replaced by its translation, `final` blocks
    and the `$display` of failures removed (the counters stay; they are harmless logic)."""
    props = find_properties(text)
    out, pos = [], 0
    for p in props:
        out.append(text[pos:p.span[0]])
        out.append(translate(p))
        pos = p.span[1]
    out.append(text[pos:])
    s = "".join(out)
    s = re.sub(r"\bfinal\s+begin.*?\bend\b", "", s, flags=re.S)
    s = re.sub(r"\bfinal\s+\$display\([^;]*\);", "", s)
    # A check written procedurally (`if (bad) fails_CHK_009++;`): reaching the increment is the failure.
    seen = {p.check for p in props}
    proc: list[str] = []

    def fail_point(m: re.Match) -> str:
        tag = m.group(1)
        proc.append(tag)
        return f"begin {m.group(0)} `ifdef NNC_FV_{tag} assert (1'b0); `endif end"
    s = re.sub(r"\bfails_(CHK_\d{3})\s*(?:\+\+|\+=\s*1|<=\s*fails_CHK_\d{3}\s*\+\s*1|=\s*fails_CHK_\d{3}\s*\+\s*1)\s*;",
               fail_point, s)
    for tag in dict.fromkeys(proc):
        if tag.replace("_", "-") not in seen:
            props.append(Prop(tag.replace("_", "-"), label=f"{tag}_procedural"))
    s = re.sub(r"\$display\s*\((?:[^()]|\([^()]*\))*\)\s*;", ";", s)
    s = _ISUNKNOWN.sub("1'b0", s)          # no X in formal
    return s, props


def _resets(iface: dict) -> list[dict]:
    """Reset ports of the interface ({name, active_low})."""
    rs = iface.get("resets") or ([iface["reset"]] if iface.get("reset") else [])
    names = {p["name"] for p in iface["ports"]}
    return [r for r in rs if isinstance(r, dict) and r.get("name") in names]


def env_module(contract: dict) -> str:
    """Code-generated environment: every reset asserted in the initial state."""
    rs = _resets(contract["interface"])
    lines = ["// Generated by NNC (nnc/formal.py): reset assumptions of the formal environment.",
             "module nnc_fv_env (", ",\n".join(f"  input logic {r['name']}" for r in rs) or "  input logic nnc_unused",
             ");"]
    lines += [f"  always @(*) if ($initstate) assume ({'!' if r.get('active_low', True) else ''}{r['name']});"
              for r in rs]
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def top_module(contract: dict, checker_modules: list[str], user_env: bool = False) -> str:
    """The test-bench top without the cover module, plus the reset environment and, when present, the
    designer's environment `nnc_env` (verif/formal/nnc_env.sv) on every port."""
    iface = contract["interface"]
    text = tb_top(contract, checker_modules).replace("`timescale 1ns/1ps\n", "")
    rs = _resets(iface)
    inst = ("  nnc_fv_env u_nnc_fv_env (" + ", ".join(f".{r['name']}({r['name']})" for r in rs) + ");\n") if rs else ""
    if user_env:
        params = [p for p in iface["parameters"] if not p.get("derived")]
        pmap = (" #(" + ", ".join(f".{p['name']}({p['name']})" for p in params) + ")") if params else ""
        conns = ",\n    ".join(f".{p['name']}({p['name']})" for p in iface["ports"])
        inst += f"  nnc_env{pmap} u_nnc_env (\n    {conns}\n  );\n"
    return text.replace("endmodule", inst + "endmodule").replace("module nnc_tb_top", "module nnc_fv_top")


SBY = """[tasks]
bmc
prove
cover

[options]
bmc: mode bmc
prove: mode prove
cover: mode cover
depth {depth}
multiclock {multiclock}
timeout {timeout}

[engines]
smtbmc {solver}

[script]
{read}
prep -top nnc_fv_top
setundef -zero -init {checkers}

[files]
{files}
"""


def build(contract: dict, rtl_dir: Path, sva_dir: Path, env_file: Path | None, *, depth: int = DEFAULT_DEPTH,
          defines: list[str] | None = None, solver: str = "yices", params: dict | None = None,
          task_timeout_s: int = DEFAULT_TIMEOUT_S) -> tuple[dict, list[Prop]]:
    """Input files of the formal run: per supported check an .sby project, plus the shared sources."""
    rtl = rtl_files(rtl_dir)
    chk = [f for f in checker_files(sva_dir) if f.name.startswith("nnc_chk_")]
    files: dict[str, object] = {f"src/{f.name}": f for f in rtl}
    props: list[Prop] = []
    used = []
    for f in chk:
        view, ps = formal_view(f.read_text(encoding="utf-8"))
        why = nonsynth(view)
        if why:          # a simulation-only checker (event timing, scoreboard queue): not in the formal top
            for p in ps:
                p.unsupported = p.unsupported or f"checker {f.stem} is simulation-only: {why}"
            props += ps
            continue
        files[f"src/{f.name}"] = view
        props += ps
        used.append(f)
    files["src/nnc_fv_env.sv"] = env_module(contract)
    user_env = bool(env_file and env_file.is_file())
    if user_env:
        files["src/nnc_env.sv"] = env_file
    files["src/nnc_fv_top.sv"] = top_module(contract, [f.stem for f in used], user_env)
    srcs = [k[4:] for k in files if k.startswith("src/")]
    defs = " ".join(f"-D{d}" for d in (defines or []))
    gen = " ".join(f"-chparam {k} {v} nnc_fv_top" for k, v in (params or {}).items())
    multiclock = "on" if is_async(contract["interface"]) else "off"
    # Checker variables start at 0 as in simulation (2-state int/bit); DUT flops keep a free initial value.
    checker_sel = " ".join(f"*{f.stem}*" for f in used) or "nnc_fv_top"
    for cid in sorted({p.check for p in props if not p.unsupported}):
        tag = cid.replace("-", "_")
        read = f"read_verilog -sv -formal {defs} -DNNC_FV_{tag} " + " ".join(srcs)
        if gen:
            read += f"\n{gen}"
        files[f"{tag}.sby"] = SBY.format(depth=depth, multiclock=multiclock, solver=solver, read=read,
                                          timeout=task_timeout_s, checkers=checker_sel,
                                          files="\n".join(f"src/{s}" for s in srcs))
    files["src_list.txt"] = "\n".join(srcs) + "\n"
    return files, props


RUN = ("ls CHK_*.sby | xargs -P {parallel} -I{{}} sh -c 'sby -f {{}} > \"$(basename {{}} .sby).log\" 2>&1; "
       "echo \"NNC_SBY_RC=$?\" >> \"$(basename {{}} .sby).log\"'\n")


def parse_status(out_dir: Path, tag: str) -> dict:
    """Result of one check from its two task folders (bmc, prove)."""
    def status(task: str) -> str | None:
        f = out_dir / f"{tag}_{task}" / "status"
        return f.read_text(encoding="utf-8").split()[0].strip() if f.is_file() else None
    bmc, prove, cover = status("bmc"), status("prove"), status("cover")
    log = (out_dir / f"{tag}.log").read_text(encoding="utf-8", errors="replace") if (out_dir / f"{tag}.log").is_file() else ""
    trace = sorted(str(p.relative_to(out_dir)) for p in out_dir.glob(f"{tag}_bmc/engine_*/trace*.vcd"))
    step = re.search(r"Assert failed in .*?\n.*?step (\d+)|BMC failed.*?step (\d+)|failed assertion.*?step (\d+)", log, re.S)
    if cover == "FAIL":
        st = "VACUOUS"           # the antecedent never matches within the depth: the proof says nothing
    elif prove == "PASS":
        st = "PROVEN"
    elif bmc == "FAIL":
        st = "CEX"
    elif bmc == "PASS":
        st = "BOUNDED"
    elif "TIMEOUT" in (bmc, prove, cover):
        st = "TIMEOUT"           # the solver did not finish within the time limit: nothing concluded
    else:
        st = "ERROR"
    rec = {"status": st, "bmc": bmc, "prove": prove, "cover": cover, "traces": trace}
    if st == "ERROR":
        errs = [ln for ln in log.splitlines() if "ERROR" in ln or "error" in ln.lower()][:8]
        rec["errors"] = errs or log.splitlines()[-8:]
    if step:
        rec["cex_step"] = int(next(g for g in step.groups() if g))
    return rec


def run(host: SimHost, contract: dict, rtl_dir: Path, sva_dir: Path, env_file: Path | None = None, *,
        depth: int = DEFAULT_DEPTH, defines: list[str] | None = None, parallel: int = 4,
        task_timeout_s: int = DEFAULT_TIMEOUT_S) -> dict:
    files, props = build(contract, rtl_dir, sva_dir, env_file, depth=depth, defines=defines,
                         task_timeout_s=task_timeout_s)
    n = len([k for k in files if k.endswith(".sby")])
    timeout_s = 600 + 3 * task_timeout_s * max(1, -(-n // max(1, parallel)))
    res = host.run(files, RUN.format(parallel=parallel),
                   ["CHK_*.log", "CHK_*_bmc/status", "CHK_*_prove/status", "CHK_*_bmc/engine_*/trace*.vcd",
                    "CHK_*_cover/status",
                    "CHK_*_bmc/logfile.txt", "CHK_*_prove/logfile.txt"], timeout_s=timeout_s, tag="formal")
    checks = {}
    by_check: dict[str, list[Prop]] = {}
    for p in props:
        by_check.setdefault(p.check, []).append(p)
    for cid, ps in by_check.items():
        bad = [f"a_{p.label}: {p.unsupported}" for p in ps if p.unsupported]
        if len(bad) == len(ps):
            checks[cid] = {"status": "UNSUPPORTED", "reason": "; ".join(bad)}
            continue
        checks[cid] = parse_status(res.out_dir, cid.replace("-", "_"))
        if bad:      # some assertions of the check could not be translated: the result covers the others
            checks[cid]["reason"] = "not translated: " + "; ".join(bad)
            checks[cid]["partial"] = True
    counts: dict[str, int] = {}
    for v in checks.values():
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    return {"depth": depth, "task_timeout_s": task_timeout_s, "clocks": "multiclock (free clocks)" if is_async(contract["interface"]) else "one global clock",
            "defines": defines or [], "environment": "reset assumptions" + (" + verif/formal/nnc_env.sv" if env_file and env_file.is_file() else ""),
            "checks": dict(sorted(checks.items())), "by_status": dict(sorted(counts.items())),
            "out_dir": str(res.out_dir)}


def to_markdown(name: str, res: dict, contract: dict) -> str:
    titles = {c["id"]: c["title"] for c in contract["checks"]}
    out = [f"# Formal check — {name}", "",
           f"SymbiYosys on the generated assertions, translated to immediate form by `nnc/formal.py`. Depth "
           f"{res['depth']} cycles, {res['clocks']}, environment: {res['environment']}"
           + (f", defines {', '.join(res['defines'])}" if res["defines"] else "") + ".", "",
           "- **PROVEN**: holds in every reachable state (k-induction).",
           f"- **BOUNDED**: no counterexample within {res['depth']} cycles from reset; induction inconclusive.",
           "- **CEX**: a counterexample exists. Either a design bug, or an input sequence the environment "
           "should forbid (a missing assumption). The trace (VCD) shows which.",
           "- **VACUOUS**: the antecedent cannot occur within the depth under the assumptions: the "
           "environment is too strict (or the condition is unreachable); the other results say nothing.",
           "- **UNSUPPORTED**: the assertion uses SVA outside the translated subset, or its checker is "
           "simulation-only (event timing, queues); not checked.",
           f"- **TIMEOUT**: the solver did not finish within {res.get('task_timeout_s')} s per task; nothing concluded.", "",
           f"**Result:** {res['by_status']}", "", "| Check | Title | Formal | Detail |", "|---|---|---|---|"]
    for cid, v in res["checks"].items():
        det = v.get("reason") or ("trace: " + ", ".join(v["traces"][:1]) if v.get("traces") else "") \
            or ("; ".join(v.get("errors", [])[:2]))
        out.append(f"| {cid} | {titles.get(cid, '')} | **{v['status']}** | {det.replace('|', '/')[:200]} |")
    return "\n".join(out) + "\n"


def write(work: Path, name: str, res: dict, contract: dict) -> None:
    (work / "formal.json").write_text(json.dumps({k: v for k, v in res.items() if k != "out_dir"}, indent=1) + "\n",
                                      encoding="utf-8")
    (work / "formal.md").write_text(to_markdown(name, res, contract), encoding="utf-8")


# ---------------------------------------------------------------------------------- counterexample triage
def vcd_table(path: Path, keep: re.Pattern | None = None, max_chars: int = 7000) -> str:
    """A counterexample trace as a table: one row per changing signal (top-level ports, and the signals of
    the scopes matching `keep`), one column per clock step (rising edges at the sampled times)."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    head, _, body = txt.partition("$enddefinitions")
    ids: dict[str, list[str]] = {}
    stack: list[str] = []
    for line in head.splitlines():
        m = re.match(r"\s*\$scope \w+ (\S+)", line)
        if m:
            stack.append(m.group(1))
            continue
        if "$upscope" in line:
            stack.pop()
            continue
        m = re.match(r"\s*\$var \w+ \d+ (\S+) (\S+)", line)
        if m:
            name = "/".join(stack[1:] + [m.group(2)])
            top = len(stack) == 1
            if top or (keep and keep.search(name) and len(stack) == 2):
                ids.setdefault(m.group(1), []).append(name)
    cur: dict[str, str] = {}
    rows: list[tuple[int, dict]] = []
    t = None
    for line in body.splitlines():
        if line.startswith("#"):
            if t is not None:
                rows.append((t, dict(cur)))
            t = int(line[1:])
            continue
        m = re.match(r"^b(\S+) (\S+)$", line) or re.match(r"^([01xz])(\S+)$", line)
        if m:
            for n in ids.get(m.group(2), []):
                cur[n] = m.group(1)
    if t is not None:
        rows.append((t, dict(cur)))
    times = sorted({tt for tt, _ in rows})
    step = min((b - a for a, b in zip(times, times[1:])), default=1) * 2 or 1
    rows = [r for r in rows if r[0] % step == 0] or rows

    def fmt(v: str) -> str:
        if not v or not set(v) <= {"0", "1"}:
            return v
        n = int(v, 2)
        return str(n) if n < 100000 else hex(n)
    lines = ["signal".ljust(40) + " ".join(f"{i:>10}" for i in range(len(rows)))]
    for n in sorted({n for _, r in rows for n in r}):
        vals = [r.get(n, "-") for _, r in rows]
        if len(set(vals)) == 1 and "/" in n:
            continue
        lines.append(n[:40].ljust(40) + " ".join(f"{fmt(v)[:10]:>10}" for v in vals))
    out = "\n".join(lines)
    return out if len(out) <= max_chars else out[:max_chars] + "\n... (truncated)"


TRIAGE_SCHEMA = {
    "type": "object", "required": ["analyses"], "additionalProperties": False,
    "properties": {"analyses": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["check", "what_happens", "spec_says", "rtl_does", "checker_does", "candidates", "most_likely",
                     "options"],
        "properties": {
            "check": {"type": "string"}, "what_happens": {"type": "string"}, "spec_says": {"type": "string"},
            "rtl_does": {"type": "string"}, "checker_does": {"type": "string"},
            "candidates": {"type": "array", "items": {
                "type": "object", "required": ["cause", "evidence_for", "evidence_against"], "additionalProperties": False,
                "properties": {"cause": {"type": "string", "enum": ["A_rtl_wrong", "B_checker_wrong", "C_spec_unclear",
                                                                    "E_environment_missing"]},
                               "evidence_for": {"type": "string"}, "evidence_against": {"type": "string"}}}},
            "most_likely": {"type": "string", "enum": ["A_rtl_wrong", "B_checker_wrong", "C_spec_unclear",
                                                       "E_environment_missing", "undetermined"]},
            "options": {"type": "string"}}}}},
}
TRIAGE_SYSTEM = (
    "You are a senior formal-verification engineer analysing counterexamples. You read the files in the current "
    "directory with the tools you have. You do not decide; you give the designer the evidence. Quote files with "
    "line numbers. Return the answer in the required JSON structure."
)


def triage_cex(res: dict, contract: dict, files: dict[str, Path], traces: dict[str, Path], backend, log_dir: Path, *,
               model: str = "opus", max_checks: int = 10) -> dict:
    """Agent A14 (sandbox, reads spec, contract, checkers, environment and RTL; changes nothing): for each
    counterexample, the most likely cause: RTL wrong, checker wrong, specification unclear, or an
    environment obligation missing from verif/formal/nnc_env.sv (an input sequence the spec forbids)."""
    from nnc.agents.backend import AgentTask
    from nnc.agents.runtime import Usage
    cex = [cid for cid, v in res["checks"].items() if v["status"] == "CEX" and cid in traces][:max_checks]
    if not cex:
        return {"analyses": [], "checks": 0}
    titles = {c["id"]: c for c in contract["checks"]}
    blocks = []
    for cid in cex:
        tag = cid.replace("-", "_")
        table = vcd_table(traces[cid], re.compile(r"^u_nnc_chk_"))
        c = titles.get(cid, {})
        blocks.append(f"### {cid}: {c.get('title', '')}\nBEHAVIOR: {c.get('behavior', '')}\n"
                      f"Assertion label(s): a_{tag}* in verif/sva/. Counterexample (one column per clock step from reset; "
                      f"top-level ports, then signals of the checker modules):\n```\n{table}\n```")
    listing = "\n".join(f"  {n}" for n in sorted(files))
    instructions = (
        "FILES IN THIS DIRECTORY\n" + listing + "\n\nThe formal tool (SymbiYosys, " + res.get("clocks", "") +
        ", depth " + str(res.get("depth")) + ") found an input sequence that breaks each assertion below, under the "
        "reset assumptions and the environment assumptions of verif/formal/nnc_env.sv. Simulation never produced "
        "these sequences.\n\n" + "\n\n".join(blocks) +
        "\n\nFor each counterexample: say in what_happens what the inputs do and where the assertion fails; read the "
        "rule quotes in contract.json and rules.json and the specification (spec_says, quote + file:line); read the RTL "
        "(rtl_does, file:line) and the checker (checker_does, file:line). Candidates: A_rtl_wrong (the DUT breaks the "
        "specification for a legal input sequence), B_checker_wrong (the assertion or its helper logic does not match "
        "the specification), C_spec_unclear, E_environment_missing (the input sequence breaks an obligation the "
        "specification places on the environment, which nnc_env.sv does not yet assume: name the rule). Give most_likely "
        "and options (the change each choice needs). Do not propose weakening a check or an assumption that the "
        "specification does not support.")
    usage = Usage()
    task = AgentTask("A14_formal_triage", instructions, TRIAGE_SCHEMA, inputs=dict(files), tools=("Read", "Grep", "Glob"),
                     system_prompt=TRIAGE_SYSTEM, model=model, max_turns=60)
    r = backend.run(task, log_dir)
    usage.add(r)
    return {"analyses": r.output["analyses"], "checks": len(cex), "usage": usage.as_dict()}


def triage_markdown(name: str, tri: dict) -> str:
    out = [f"# Formal counterexample triage — {name}", "",
           f"Counterexamples analysed: {tri.get('checks', 0)}. Causes: A = RTL wrong, B = checker wrong, C = specification "
           "unclear, E = an environment obligation missing from verif/formal/nnc_env.sv. The designer decides; "
           "nothing was changed.", ""]
    for a in tri.get("analyses", []):
        out += [f"## {a['check']} — most likely **{a['most_likely']}**", "", "| Part | Content |", "|---|---|",
                f"| What happens | {a['what_happens']} |", f"| Specification says | {a['spec_says']} |",
                f"| RTL does | {a['rtl_does']} |", f"| Checker does | {a['checker_does']} |"]
        out += [f"| {c['cause']} | For: {c['evidence_for']}<br>Against: {c['evidence_against']} |" for c in a["candidates"]]
        out += [f"| Options | {a['options']} |", ""]
    return "\n".join(x.replace("\n", " ") if x.startswith("|") else x for x in out) + "\n"
