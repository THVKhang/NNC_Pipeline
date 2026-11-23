"""Intake: what the flow can do with a new specification and a new RTL, before any agent runs (no tokens).

    rtl/ (+ library folders)  ->  file closure of the top  ->  four tool runs  ->  ports, clocks, resets, constructs
    specification              ->  specdraft.check_spec

Every input gets one of four verdicts, never a silent wrong result (docs/INPUT_SUPPORT.md):
* ready        the flow runs on it as it is;
* adapt        the flow runs after a generated, recorded adaptation (nnc adapt: a wrapper that flattens struct
               and array ports; an interface document derived from the port declarations);
* needs_input  the designer must give something the inputs do not say (the top module among several
               candidates, a missing package or include file, a specification the flow cannot read);
* unsupported  the flow cannot run on it (VHDL, encrypted source, a port type no adapter handles), with the
               reason.

What is read from the RTL: file and unit names, the port declarations of the top (through Verilator's elaborated
tree), and the structure of the flattened Yosys netlist (which top inputs clock or reset flops, latches,
memories, tri-states). No behaviour of the RTL reaches an agent: work/intake.json is not in any agent packet.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

SV_EXT = (".sv", ".v")
HDR_EXT = (".svh", ".vh", ".inc")
VHDL_EXT = (".vhd", ".vhdl")
VERDICTS = ("ready", "adapt", "needs_input", "unsupported")

# ------------------------------------------------------------------------------------ source scanning
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_DECL = re.compile(r"^[ \t]*(?:extern\s+)?(module|macromodule|interface|package|program)\s+"
                   r"(?:(?:automatic|static)\s+)?([A-Za-z_]\w*)", re.M)
_END = {"module": "endmodule", "macromodule": "endmodule", "interface": "endinterface", "package": "endpackage",
        "program": "endprogram"}
_INCLUDE = re.compile(r'`include\s+"([^"]+)"')
_PKG_REF = re.compile(r"\b([A-Za-z_]\w*)\s*::")
# `name #(`  or  `name inst (`  or  `name inst [N] (`: an instance of module `name`
_INST = re.compile(r"\b([A-Za-z_]\w*)\s*(?:#\s*\(|\s[A-Za-z_]\w*\s*(?:\[[^\]]*\]\s*)*\()")
_WORD = re.compile(r"\b([A-Za-z_]\w*)\b")
_PROTECT = re.compile(r"`(?:pragma\s+)?protect\b|`protected\b")
_STD_PACKAGES = {"std", "$unit", "uvm_pkg"}


def strip_comments(text: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text))


def scan(text: str) -> dict:
    """Units a file declares, and the names it refers to (approximate; the tools confirm)."""
    code = strip_comments(text)
    units, refs = [], {"package": set(), "instance": set(), "word": set()}
    for m in _DECL.finditer(code):
        kind, name = m.group(1), m.group(2)
        units.append({"kind": "module" if kind == "macromodule" else kind, "name": name})
    refs["package"] = {m.group(1) for m in _PKG_REF.finditer(code)}
    refs["instance"] = {m.group(1) for m in _INST.finditer(code)}
    refs["word"] = set(_WORD.findall(code))
    return {"units": units, "refs": refs, "includes": _INCLUDE.findall(code),
            "protected": bool(_PROTECT.search(text))}


def _sources(folder: Path, recursive: bool) -> list[Path]:
    pats = ("**/*" if recursive else "*")
    return sorted(p for p in folder.glob(pats) if p.is_file() and p.suffix.lower() in SV_EXT + HDR_EXT + VHDL_EXT)


def collect(primary: Path, libs: list[Path] | None = None, top: str | None = None,
            listed: list[Path] | None = None) -> dict:
    """The files the top needs, in compile order.

    primary: the design's RTL folder; its files win over library files of the same unit name.
    libs: folders searched (recursively) for units the primary files refer to.
    listed: the primary files in a given order (rtl/filelist.f), else every source file of `primary`.
    top: the top module; when None, the modules of the primary files that no primary file instantiates."""
    libs = libs or []
    prim = listed if listed else [p for p in _sources(primary, False) if p.suffix.lower() in SV_EXT]
    vhdl = [p for p in _sources(primary, True) if p.suffix.lower() in VHDL_EXT]
    lib_files = [p for lib in libs for p in _sources(lib, True) if p.suffix.lower() in SV_EXT]
    info: dict[Path, dict] = {}
    for p in prim + lib_files:
        if p not in info:
            info[p] = scan(p.read_text(encoding="utf-8", errors="replace"))
    decl: dict[str, list[tuple[Path, str]]] = {}
    for p in prim + [x for x in lib_files if x not in prim]:
        for u in info[p]["units"]:
            decl.setdefault(u["name"], []).append((p, u["kind"]))
    kinds = {n: v[0][1] for n, v in decl.items()}
    duplicates = {n: [str(f) for f, _ in v] for n, v in decl.items() if len({f for f, _ in v}) > 1}

    def refs_of(p: Path) -> set[str]:
        r = info[p]["refs"]
        own = {u["name"] for u in info[p]["units"]}
        out = {n for n in r["package"] if kinds.get(n) == "package"}
        out |= {n for n in r["instance"] if kinds.get(n) in ("module", "program")}
        out |= {n for n in r["word"] if kinds.get(n) == "interface"}
        return out - own

    prim_modules = [u["name"] for p in prim for u in info[p]["units"] if u["kind"] == "module"]
    instantiated = {n for p in prim for n in refs_of(p)}
    candidates = [m for m in dict.fromkeys(prim_modules) if m not in instantiated]
    out = {"top": top, "candidates": candidates, "duplicates": duplicates, "vhdl": [str(p) for p in vhdl],
           "protected": [str(p) for p in prim + lib_files if info[p]["protected"]],
           "files": [], "include_dirs": [], "missing_includes": [], "missing_packages": []}
    if top is None:
        if len(candidates) != 1:
            return out
        top = out["top"] = candidates[0]
    if top not in decl or kinds[top] != "module":
        out["missing_top"] = True
        return out

    need: list[Path] = []
    seen_units: set[str] = set()
    queue = [top]
    while queue:
        name = queue.pop(0)
        if name in seen_units or name not in decl:
            continue
        seen_units.add(name)
        f = decl[name][0][0]
        if f not in need:
            need.append(f)
            queue += sorted(refs_of(f))
    for f in need:
        missing = {n for n in info[f]["refs"]["package"] if n not in decl and n not in _STD_PACKAGES
                   and not n[0].isupper() and f"{n}" not in {u["name"] for u in info[f]["units"]}}
        # `x::` is also a class scope or an enum of a package; only names that look like packages count
        out["missing_packages"] += sorted(n for n in missing if n.endswith("_pkg"))
    out["missing_packages"] = sorted(set(out["missing_packages"]))

    # includes: the including file's folder, the primary folder, then the library folders (recursively)
    search = [primary] + [d for lib in libs for d in [lib, *sorted(x for x in lib.rglob("*") if x.is_dir())]]
    inc_dirs: list[Path] = []
    todo = [(f, i) for f in need for i in info[f]["includes"]]
    done: set[str] = set()
    while todo:
        f, inc = todo.pop(0)
        if inc in done:
            continue
        done.add(inc)
        hit = next((d / inc for d in [f.parent] + search if (d / inc).is_file()), None)
        if hit is None:
            out["missing_includes"].append(inc)
            continue
        d = hit.parent if "/" not in inc else Path(str(hit)[: -len(inc)].rstrip("/\\"))
        if d not in inc_dirs:
            inc_dirs.append(d)
        todo += [(hit, i) for i in scan(hit.read_text(encoding="utf-8", errors="replace"))["includes"]]
    out["include_dirs"] = [str(d) for d in inc_dirs]

    # order: packages (dependencies first), interfaces, then the rest in the order found
    def unit_kinds(f: Path) -> set[str]:
        return {u["kind"] for u in info[f]["units"]}

    pk = [f for f in need if "package" in unit_kinds(f)]
    ordered: list[Path] = []
    visiting: set[Path] = set()

    def visit(f: Path) -> None:
        if f in ordered or f in visiting:
            return
        visiting.add(f)
        for n in sorted(refs_of(f)):
            g = decl[n][0][0]
            if g in pk:
                visit(g)
        visiting.discard(f)
        ordered.append(f)

    for f in pk:
        visit(f)
    ordered += [f for f in need if f not in ordered and "interface" in unit_kinds(f)]
    if listed:   # keep the given order for the primary files
        ordered += [f for f in listed if f in need and f not in ordered]
    ordered += [f for f in need if f not in ordered]
    out["files"] = [str(f) for f in ordered]
    out["library_files"] = [str(f) for f in ordered if f not in prim]
    return out


# ------------------------------------------------------------------------------------ tool runs
def probe_files(files: list[str], include_dirs: list[str]) -> tuple[dict[str, Path], list[str], list[str]]:
    """Host file map (src/<k>/<name>, one folder per source folder, so include paths keep working),
    the ordered source paths and the include paths on the host."""
    folders: list[str] = []
    fmap: dict[str, Path] = {}
    srcs, incs = [], []

    def host_dir(d: str) -> str:
        if d not in folders:
            folders.append(d)
        return f"src/{folders.index(d)}"

    for f in files:
        p = Path(f)
        k = f"{host_dir(str(p.parent))}/{p.name}"
        fmap[k] = p
        srcs.append(k)
    for d in include_dirs:
        hd = host_dir(d)
        incs.append(hd)
        for h in Path(d).rglob("*"):
            if h.is_file() and h.suffix.lower() in HDR_EXT + SV_EXT:
                fmap.setdefault(f"{hd}/{h.relative_to(d).as_posix()}", h)
    return fmap, srcs, incs


def probe_script(top: str, srcs: list[str], incs: list[str], defines: list[str] | None = None,
                 params: dict[str, int] | None = None) -> str:
    """Four runs, each recorded by its exit code: Verilator lint, Verilator elaborated tree, Yosys with its
    Verilog frontend and with yosys-slang (proc; flatten; opt_dff: opt_dff turns a flop whose next value is a
    constant under a port into a flop with a synchronous reset, so that synchronous resets are found)."""
    d = " ".join(f"-D{x}" for x in defines or [])
    vi = " ".join(f"+incdir+{i}" for i in incs)
    yi = " ".join(f"-I{i}" for i in incs)
    si = " ".join(f"-I {i}" for i in incs)
    g = " ".join(f"-G{k}={v}" for k, v in (params or {}).items())
    chp = "".join(f" -chparam {k} {v}" for k, v in (params or {}).items())
    sg = "".join(f" -G {k}={v}" for k, v in (params or {}).items())
    s = " ".join(srcs)
    vopt = f"-Wno-fatal -Wno-lint -Wno-style --top-module {top} {g} {d} {vi} {s}"
    return "\n".join([
        f"verilator --lint-only {vopt} > lint.log 2>&1; echo NNC_LINT=$?",
        f"verilator --json-only --Mdir j {vopt} > json.log 2>&1; echo NNC_JSON=$?",
        f"yosys -q -p 'read_verilog -sv {d} {yi} {s}; hierarchy -top {top}{chp}; proc; flatten; opt_dff; opt_clean; "
        f"write_json y_verilog.json' > y_verilog.log 2>&1; echo NNC_YOSYS=$?",
        f"yosys -q -p 'read_slang {d} {si} --top {top}{sg} {s}; hierarchy -top {top}; proc; flatten; opt_dff; opt_clean; "
        f"write_json y_slang.json' > y_slang.log 2>&1; echo NNC_SLANG=$?",
    ])


PROBE_OUTPUTS = ["j/*.tree.json", "y_verilog.json", "y_slang.json", "lint.log", "json.log", "y_verilog.log",
                 "y_slang.log"]


def probe_codes(output: str) -> dict[str, int | None]:
    out = {}
    for k in ("LINT", "JSON", "YOSYS", "SLANG"):
        m = re.search(rf"NNC_{k}=(\d+)", output)
        out[k.lower()] = int(m.group(1)) if m else None
    return out


def first_errors(log: str, n: int = 5) -> list[str]:
    lines = [l.strip() for l in log.splitlines() if re.match(r"\s*(%Error|ERROR|error|.*: error:)", l)]
    return (lines or [l.strip() for l in log.splitlines() if l.strip()][-n:])[:n]


# ------------------------------------------------------------------------------------ ports (Verilator tree)
def _index(n, nodes: dict) -> None:
    if isinstance(n, dict):
        if "addr" in n:
            nodes.setdefault(n["addr"], n)
        for v in n.values():
            _index(v, nodes)
    elif isinstance(n, list):
        for v in n:
            _index(v, nodes)


_RANGE = re.compile(r"^\s*\[?\s*(-?\d+)\s*:\s*(-?\d+)\s*\]?\s*$")
_KEYWORD_W = {"logic": 1, "bit": 1, "reg": 1, "wire": 1, "byte": 8, "shortint": 16, "int": 32, "integer": 32,
              "longint": 64, "time": 64}
_UNSUPPORTED_KW = {"real", "shortreal", "realtime", "string", "chandle", "event"}


def _span(r: str | None) -> tuple[int, int] | None:
    m = _RANGE.match(r or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def _const(node: dict | None) -> int | None:
    """Value of a Verilator CONST node name such as 32'h1f or 32'sh8."""
    if not node:
        return None
    m = re.match(r"^(?:\d+)?'s?([hdbo])([0-9a-fA-F_]+)$", node.get("name", ""))
    if not m:
        return None
    return int(m.group(2).replace("_", ""), {"h": 16, "d": 10, "b": 2, "o": 8}[m.group(1)])


def _array_range(n: dict) -> tuple[int, int] | None:
    r = _span(n.get("declRange"))
    if r:
        return r
    for rg in n.get("rangep") or []:
        left = _const((rg.get("leftp") or [None])[0])
        right = _const((rg.get("rightp") or [None])[0])
        if left is not None and right is not None:
            return left, right
    return None


def dtype(nodes: dict, addr: str | None, depth: int = 0) -> dict:
    """{kind, width, fields, type} of a type node. kind: vector, struct (packed struct or union), packed_array,
    unpacked_array, interface, unpacked_struct, unsupported. fields: [(path, lsb, width)] of the leaves of a
    packed type, lsb from bit 0 of the whole value."""
    n = nodes.get(addr or "")
    if n is None or depth > 40:
        return {"kind": "unsupported", "width": None, "fields": [], "type": "unknown"}
    t = n.get("type")
    if t in ("REFDTYPE", "ENUMDTYPE", "CONSTDTYPE", "PARAMTYPEDTYPE", "TYPEDEF"):
        nxt = n.get("refDTypep") if n.get("refDTypep") not in (None, addr) else n.get("subDTypep")
        if nxt in (None, addr):
            nxt = n.get("dtypep") if n.get("dtypep") != addr else None
        r = dtype(nodes, nxt, depth + 1)
        if t == "ENUMDTYPE":
            r = {**r, "fields": [], "kind": "vector" if r["kind"] in ("vector", "struct", "packed_array") else r["kind"]}
        return {**r, "type": n.get("typedefName") or n.get("name") or r.get("type")}
    if t == "BASICDTYPE":
        kw = n.get("keyword") or n.get("name")
        if kw in _UNSUPPORTED_KW:
            return {"kind": "unsupported", "width": None, "fields": [], "type": kw}
        sp = _span(n.get("range"))
        w = abs(sp[0] - sp[1]) + 1 if sp else _KEYWORD_W.get(kw, 1)
        return {"kind": "vector", "width": w, "fields": [], "type": kw}
    if t in ("STRUCTDTYPE", "UNIONDTYPE"):
        if not n.get("packed"):
            return {"kind": "unpacked_struct", "width": None, "fields": [], "type": n.get("name")}
        members = n.get("membersp") or []
        fields, widths = [], []
        for mbr in members:
            md = dtype(nodes, mbr.get("dtypep") if mbr.get("dtypep") != mbr.get("addr") else mbr.get("refDTypep"),
                       depth + 1)
            if md["width"] is None:
                return {"kind": "unsupported", "width": None, "fields": [], "type": n.get("name")}
            lsb = int(mbr.get("lsb") or 0) if t == "STRUCTDTYPE" else 0
            widths.append(md["width"] + lsb)
            sub = md["fields"] or [("", 0, md["width"])]
            fields += [((mbr["name"] + ("." + p if p else "")), lsb + l, w) for p, l, w in sub]
        width = max(widths) if widths else 0
        if t == "UNIONDTYPE":     # members overlap: the union is one vector
            fields = []
        return {"kind": "struct" if fields else "vector", "width": width, "fields": fields, "type": n.get("name")}
    if t == "PACKARRAYDTYPE":
        el = dtype(nodes, n.get("refDTypep") or n.get("subDTypep"), depth + 1)
        r = _array_range(n)
        if el["width"] is None or r is None:
            return {"kind": "unsupported", "width": None, "fields": [], "type": "packed array"}
        count = abs(r[0] - r[1]) + 1
        if not el["fields"]:
            return {"kind": "vector", "width": el["width"] * count, "fields": [], "type": el["type"]}
        lo = min(r)
        fields = []
        for k in range(count):
            idx = lo + k                         # element idx sits at bits [(idx-lo)*w +: w] for [hi:lo]
            pos = (idx - lo) if r[0] >= r[1] else (count - 1 - (idx - lo))
            fields += [(f"[{idx}]" + ("." + p if p else ""), pos * el["width"] + l, w) for p, l, w in el["fields"]]
        return {"kind": "packed_array", "width": el["width"] * count, "fields": fields, "type": el["type"]}
    if t == "UNPACKARRAYDTYPE":
        el = dtype(nodes, n.get("refDTypep") or n.get("subDTypep"), depth + 1)
        r = _array_range(n)
        return {"kind": "unpacked_array", "width": el["width"], "fields": el["fields"], "type": el["type"],
                "range": list(r) if r else None, "element_kind": el["kind"]}
    if t in ("IFACEREFDTYPE",):
        return {"kind": "interface", "width": None, "fields": [], "type": n.get("ifaceName") or n.get("name")}
    return {"kind": "unsupported", "width": None, "fields": [], "type": t}


def _chain(nodes: dict, addr: str | None):
    """The type nodes from `addr` through typedefs and references."""
    seen = set()
    while addr and addr not in seen and addr in nodes:
        seen.add(addr)
        n = nodes[addr]
        yield n
        addr = n.get("refDTypep") or n.get("subDTypep") or (n.get("dtypep") if n.get("dtypep") != addr else None)


def _is_enum(nodes: dict, addr: str | None) -> bool:
    return any(n.get("type") == "ENUMDTYPE" for n in _chain(nodes, addr))


def contract_param(p: dict) -> bool:
    """A parameter of the top that the contract can carry: the contract and the test bench declare every
    parameter as `parameter int` (32-bit signed), so a value that is wider, an enum or not a number cannot be
    passed through without changing it. Such a parameter keeps the default of the RTL."""
    v = p.get("value")
    if not isinstance(v, int) or p.get("enum"):
        return False
    if p.get("width") is not None and p["width"] > 32:
        return False
    return -2 ** 31 <= v < 2 ** 31


def tree_top(tree: dict, top: str) -> dict | None:
    mods = [m for m in tree.get("modulesp") or [] if m.get("type") == "MODULE"]
    return next((m for m in mods if top in (m.get("origName"), m.get("name"))), None) or \
        next((m for m in mods if str(m.get("level")) == "1"), None)


def ports_from_tree(tree: dict, top: str) -> tuple[list[dict], list[dict]]:
    """(ports, parameters) of the top module of a Verilator --json-only tree."""
    nodes: dict = {}
    _index(tree, nodes)
    mod = tree_top(tree, top)
    if mod is None:
        return [], []
    ports, params = [], []
    for s in mod.get("stmtsp") or []:
        if s.get("type") != "VAR":
            continue
        if s.get("varType") == "GPARAM":
            d = dtype(nodes, s.get("dtypep"))
            params.append({"name": s.get("origName") or s["name"], "value": _const((s.get("valuep") or [None])[0]),
                           "width": d["width"], "enum": _is_enum(nodes, s.get("dtypep"))})
            continue
        if s.get("direction") in (None, "NONE") and s.get("varType") != "IFACEREF":
            continue
        d = dtype(nodes, s.get("dtypep"))
        if s.get("varType") == "IFACEREF":
            d = {**d, "kind": "interface"}
        ports.append({"name": s.get("origName") or s["name"], "direction": (s.get("direction") or "inout").lower(),
                      **d})
    return ports, params


PORT_HANDLING = {
    "vector": "direct",
    "struct": "adapter",           # packed struct or packed union with fields: flattened by the wrapper
    "packed_array": "adapter",     # packed array of structs
    "unpacked_array": "adapter",
    "clock_vector": "adapter",     # a vector port whose bits clock flops: one clock port per bit
    "interface": "unsupported",    # Verilator has no interface port on the top: a wrapper must instantiate it
    "unpacked_struct": "unsupported",
    "unsupported": "unsupported",
}


def mark_clock_vectors(ports: list[dict], struct: dict | None) -> None:
    """A vector port of several bits that clocks flops (`input [1:0] clks_i`) becomes kind clock_vector: the
    test bench drives one clock per port, so the wrapper splits it into one port per bit."""
    clocks = (struct or {}).get("clocks") or {}
    for p in ports:
        if p.get("kind") == "vector" and (p.get("width") or 1) > 1 and p["name"] in clocks:
            p["kind"] = "clock_vector"
            p["fields"] = [[f"[{i}]", i, 1] for i in range(p["width"])]
            p["clock_lanes"] = list(clocks[p["name"]].get("lanes") or range(p["width"]))


def port_handling(p: dict) -> str:
    h = PORT_HANDLING.get(p["kind"], "unsupported")
    if p["kind"] == "unpacked_array" and p.get("element_kind") not in ("vector", "struct", "packed_array"):
        return "unsupported"
    if p["kind"] == "unpacked_array" and not p.get("range"):
        return "unsupported"
    return h


# ------------------------------------------------------------------------------------ structure (Yosys)
_FF = {"$dff", "$dffe", "$adff", "$adffe", "$sdff", "$sdffe", "$sdffce", "$dffsr", "$dffsre", "$aldff", "$aldffe"}
_LATCH = {"$dlatch", "$adlatch", "$dlatchsr", "$sr"}


def _pint(v) -> int:
    if isinstance(v, int):
        return v
    s = str(v)
    return int(s, 2) if s and set(s) <= {"0", "1"} else int(s or 0)


def structure(netlist: dict, top: str) -> dict:
    """Clocks, resets and constructs of the flattened netlist, traced to the top's input ports."""
    mods = netlist.get("modules") or {}
    mod = mods.get(top) or next((m for m in mods.values() if str((m.get("attributes") or {}).get("top", "0")) not in
                                 ("0", "00000000000000000000000000000000")), None)
    if mod is None:
        return {"error": f"module {top} not in the netlist"}
    bit_port: dict = {}
    bit_lane: dict = {}                    # netlist bit -> its position in the port, from the LSB
    for name, p in (mod.get("ports") or {}).items():
        for i, b in enumerate(p.get("bits") or []):
            bit_port[b] = name
            bit_lane[b] = i
    clocks: dict[str, dict] = {}
    aresets: dict[str, dict] = {}
    sresets: dict[str, dict] = {}
    out = {"flop_bits": 0, "latches": 0, "memories": 0, "derived_clock_bits": 0, "tristate": False,
           "negedge_bits": 0}
    for cell in (mod.get("cells") or {}).values():
        t, prm, con = cell.get("type", ""), cell.get("parameters") or {}, cell.get("connections") or {}
        if t in _FF:
            w = _pint(prm.get("WIDTH", 1))
            out["flop_bits"] += w
            clk = (con.get("CLK") or [None])[0]
            src = bit_port.get(clk)
            if src is None:
                out["derived_clock_bits"] += w
            else:
                c = clocks.setdefault(src, {"bits": 0, "edges": set(), "lanes": set()})
                c["bits"] += w
                c["lanes"].add(bit_lane[clk])
                c["edges"].add("rise" if _pint(prm.get("CLK_POLARITY", 1)) else "fall")
            if not _pint(prm.get("CLK_POLARITY", 1)):
                out["negedge_bits"] += w
            # yosys-slang writes an asynchronous reset as an asynchronous load of a constant ($aldff)
            for pin, pol, table in (("ARST", "ARST_POLARITY", aresets), ("SRST", "SRST_POLARITY", sresets),
                                    ("ALOAD", "ALOAD_POLARITY", aresets)):
                if pin == "ALOAD" and not all(str(b) in ("0", "1") for b in con.get("AD") or []):
                    continue
                if pin in con:
                    r = bit_port.get(con[pin][0])
                    key = r or "(internal)"
                    e = table.setdefault(key, {"bits": 0, "active": set()})
                    e["bits"] += w
                    e["active"].add("high" if _pint(prm.get(pol, 1)) else "low")
            for pin in ("SET", "CLR"):
                for b in con.get(pin) or []:
                    if b in bit_port:
                        e = aresets.setdefault(bit_port[b], {"bits": 0, "active": set()})
                        e["bits"] += 1
                        e["active"].add("high" if _pint(prm.get(pin + "_POLARITY", 1)) else "low")
        elif t in _LATCH:
            out["latches"] += _pint(prm.get("WIDTH", 1))
        elif t.startswith("$mem"):
            out["memories"] += 1
        elif t == "$tribuf":
            out["tristate"] = True
        if not out["tristate"] and any("z" in [str(b) for b in bits] for bits in con.values()):
            out["tristate"] = True
    out["clocks"] = {k: {"bits": v["bits"], "edges": sorted(v["edges"]), "lanes": sorted(v["lanes"])}
                     for k, v in sorted(clocks.items())}
    out["async_resets"] = {k: {"bits": v["bits"], "active": sorted(v["active"])} for k, v in sorted(aresets.items())}
    out["sync_resets"] = {k: {"bits": v["bits"], "active": sorted(v["active"])} for k, v in sorted(sresets.items())}
    return out


# ------------------------------------------------------------------------------------ verdict
_MISSING_UNIT = re.compile(r"Cannot find file containing (module|interface|package): '?([A-Za-z_]\w*)")
_NO_DEFAULT = re.compile(r"Parameter without default value is never given value[^']*'([A-Za-z_]\w*)'")


def lint_reasons(errors: list[str]) -> list[str]:
    """What the designer must give, read from Verilator's first errors."""
    out = []
    for e in errors:
        m = _MISSING_UNIT.search(e)
        if m:
            out.append(f"{m.group(1)} {m.group(2)} is declared in no file: add the folder that has it (--lib)")
        m = _NO_DEFAULT.search(e)
        if m:
            out.append(f"parameter {m.group(1)} of the top has no default value: give one (config or run set)")
    return list(dict.fromkeys(out))


def assess(col: dict, codes: dict | None, ports: list[dict], struct: dict | None, spec: dict | None,
           spec_iface: dict | None = None, errors: dict | None = None) -> dict:
    """Verdict, reasons and the stages the flow can run."""
    reasons: list[dict] = []

    def add(level: str, msg: str) -> None:
        reasons.append({"level": level, "message": msg})

    if col.get("vhdl") and not col.get("files"):
        add("unsupported", f"VHDL source ({len(col['vhdl'])} files): the flow reads Verilog and SystemVerilog only")
    elif col.get("vhdl"):
        add("note", f"{len(col['vhdl'])} VHDL files are ignored")
    if col.get("protected"):
        add("unsupported", "encrypted (protected) source: " + ", ".join(Path(p).name for p in col["protected"][:3]))
    if not col.get("top"):
        if col.get("candidates"):
            add("needs_input", "several candidate top modules: " + ", ".join(col["candidates"][:8]) +
                " (set config top)")
        else:
            add("needs_input", "no module that no other module instantiates (set config top)")
    elif col.get("missing_top"):
        add("needs_input", f"top module {col['top']} is declared in no file")
    # a missing file blocks only when the tools fail too: an include in an `ifdef branch not taken is harmless
    read_ok = codes is not None and codes.get("lint") == 0
    for p in col.get("missing_packages") or []:
        add("note" if read_ok else "needs_input",
            f"package {p} is used but declared in no file" + (" (not needed: the tools read the RTL)" if read_ok
                                                             else " (add its folder as a library)"))
    for i in col.get("missing_includes") or []:
        add("note" if read_ok else "needs_input",
            f"include file {i} not found" + (" (in a branch not compiled: the tools read the RTL)" if read_ok
                                             else " (add its folder as a library)"))
    for name, files in (col.get("duplicates") or {}).items():
        add("note", f"unit {name} is declared in {len(files)} files; the first is used: {Path(files[0]).name}")

    stages = {k: "off" for k in ("simulation", "coverage_scope", "formal", "cdc", "mutation_equivalence")}
    frontend = None
    if codes is not None and col.get("files"):
        if codes.get("lint") != 0:
            specific = lint_reasons((errors or {}).get("lint") or [])
            for msg in specific:
                add("needs_input", msg)
            if not specific:
                first = ((errors or {}).get("lint") or ["see the lint log"])[0]
                add("needs_input", f"Verilator cannot read the RTL: {first[:200]}")
        if codes.get("json") == 0 and codes.get("yosys") == 0:
            frontend = "verilog"
        elif codes.get("slang") == 0:
            frontend = "slang"
        if frontend is None:
            add("note", "neither Yosys frontend reads the RTL: formal, CDC and the constant-bit coverage scope are off")
        handling = Counter(port_handling(p) for p in ports)
        bad = [p for p in ports if port_handling(p) == "unsupported"]
        for p in bad:
            add("unsupported", f"port {p['name']}: {p['kind']} ({p.get('type')}) has no adapter yet")
        if handling.get("adapter"):
            names = [p["name"] for p in ports if port_handling(p) == "adapter"]
            add("adapt", f"{len(names)} struct, array or clock-vector ports are flattened by a generated wrapper (nnc adapt): "
                + ", ".join(names[:8]))
        inouts = [p["name"] for p in ports if p["direction"] == "inout"]
        if inouts:
            add("note", "inout ports are driven as inputs; tri-state behaviour is not checked: " + ", ".join(inouts))
        sim_ok = codes.get("lint") == 0 and codes.get("json") == 0 and not bad
        stages["simulation"] = "on" if sim_ok else "off"
        stages["coverage_scope"] = "on" if sim_ok and frontend else ("partial" if sim_ok else "off")
        if frontend:
            stages["formal"] = stages["cdc"] = stages["mutation_equivalence"] = f"on ({frontend})"
        if struct and not struct.get("error"):
            if not struct["clocks"] and struct["flop_bits"]:
                add("note", "no flop is clocked by a top input")
            if struct["derived_clock_bits"]:
                add("note", f"{struct['derived_clock_bits']} flop bits use a derived or gated clock: the CDC check "
                            f"lists them (DERIVED_CLOCK)")
            if struct["latches"]:
                add("note", f"{struct['latches']} latch bits: simulation and formal run; RTL rule RR-04 forbids "
                            f"latches in generated RTL")
            if struct["tristate"]:
                add("note", "tri-state logic: not checked")
            if struct["negedge_bits"]:
                add("note", f"{struct['negedge_bits']} flop bits on the falling edge")
            if len(struct["clocks"]) > 1:
                add("note", f"{len(struct['clocks'])} clock inputs: the specification must say whether they are "
                            f"synchronous (CDC check)")
    if spec is not None:
        errs = [f["message"] for f in spec.get("findings", []) if f["severity"] == "error"]
        if errs:
            add("adapt" if ports else "needs_input",
                "the specification has no port table the flow can read: " + errs[0] +
                ("; nnc adapt writes the interface document from the port declarations" if ports else ""))
    if spec_iface and ports:
        have = {p["name"] for p in ports}
        missing = [p for p in spec_iface.get("ports", []) if p not in have]
        if missing and not any(p["kind"] != "vector" for p in ports):
            add("note", "ports of the specification's table that the top does not have: " + ", ".join(missing[:8]))
    level = "ready"
    for v in ("adapt", "needs_input", "unsupported"):
        if any(r["level"] == v for r in reasons):
            level = v
    return {"verdict": level, "reasons": reasons, "frontend": frontend, "stages": stages}


# ------------------------------------------------------------------------------------ the whole intake
def run(host, rtl_dir: Path, *, top: str | None = None, libs: list[Path] | None = None,
        listed: list[Path] | None = None, defines: list[str] | None = None, params: dict[str, int] | None = None,
        spec: Path | None = None, timeout_s: int = 900, keep: Path | None = None) -> dict:
    """Intake of one RTL folder (and its specification). `host` None: source scan only."""
    from nnc import specdraft
    col = collect(rtl_dir, libs, top, listed)
    rep: dict = {"rtl_dir": str(rtl_dir), "libraries": [str(x) for x in libs or []], "collect": col,
                 "codes": None, "ports": [], "parameters": [], "structure": None, "errors": {}}
    if host is not None and col.get("files") and not col.get("protected"):
        fmap, srcs, incs = probe_files(col["files"], col["include_dirs"])
        res = host.run(fmap, probe_script(col["top"], srcs, incs, defines, params), PROBE_OUTPUTS,
                       timeout_s=timeout_s, tag="intake")
        rep["codes"] = codes = probe_codes(res.output)
        for k, log in (("lint", "lint.log"), ("json", "json.log"), ("yosys", "y_verilog.log"),
                       ("slang", "y_slang.log")):
            f = res.out_dir / log
            if codes.get(k) not in (0, None) and f.is_file():
                rep["errors"][k] = first_errors(f.read_text(encoding="utf-8", errors="replace"))
        trees = sorted((res.out_dir / "j").glob("*.tree.json")) if (res.out_dir / "j").is_dir() else []
        if trees:
            tree = json.loads(trees[0].read_text(encoding="utf-8"))
            rep["ports"], rep["parameters"] = ports_from_tree(tree, col["top"])
            for p in rep["ports"]:
                p["fields"] = [list(f) for f in p.get("fields", [])]
        for name in ("y_verilog.json", "y_slang.json"):
            f = res.out_dir / name
            if f.is_file():
                try:
                    rep["structure"] = structure(json.loads(f.read_text(encoding="utf-8")), col["top"])
                    rep["structure"]["from"] = name
                    break
                except (ValueError, KeyError) as e:
                    rep["errors"]["structure"] = [str(e)]
        mark_clock_vectors(rep["ports"], rep["structure"])
        if keep is not None and trees:
            keep.mkdir(parents=True, exist_ok=True)
            (keep / "intake_tree.json").write_bytes(trees[0].read_bytes())
    spec_res = None
    spec_iface = None
    if spec is not None:
        spec_res = specdraft.check_spec(spec, col.get("top"))
        rep["spec"] = {"file": str(spec), **spec_res}
    rep.update(assess(col, rep["codes"], rep["ports"], rep["structure"], spec_res, spec_iface, rep["errors"]))
    return rep


def portable(obj, *bases: Path):
    """`obj` with every path under one of `bases` written relative to it, with forward slashes: the reports
    are committed, so they hold no local folder (user name, temporary directory)."""
    prefixes = []
    for b in bases:
        for s in {str(b), str(Path(b).resolve())}:
            prefixes += [s.rstrip("\\/") + "\\", s.rstrip("\\/") + "/"]
    prefixes.sort(key=len, reverse=True)

    def one(x):
        if isinstance(x, str):
            for pre in prefixes:
                if x.startswith(pre):
                    return x[len(pre):].replace("\\", "/")
                if x == pre[:-1]:
                    return "."
            return x
        if isinstance(x, dict):
            return {k: one(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [one(v) for v in x]
        return x
    return one(obj)


def to_markdown(rep: dict, title: str) -> str:
    col = rep["collect"]
    L = [f"# Intake: {title}", "",
         "Generated by `nnc intake` (no agent). What the flow can do with these inputs, before any agent runs. "
         "Verdicts: ready, adapt (a generated, recorded adaptation first), needs_input, unsupported. "
         "See docs/INPUT_SUPPORT.md.", "",
         f"**Verdict: {rep['verdict']}**", ""]
    if rep["reasons"]:
        L += ["| Level | Finding |", "|---|---|"]
        L += [f"| {r['level']} | {r['message']} |" for r in rep["reasons"]]
        L.append("")
    L += ["## RTL", "",
          f"- top: `{col.get('top')}`" + (f" (candidates: {', '.join(col['candidates'])})" if not col.get("top") else ""),
          f"- files: {len(col.get('files') or [])}, of which {len(col.get('library_files') or [])} from libraries",
          f"- include folders: {len(col.get('include_dirs') or [])}"]
    if rep.get("codes"):
        c = rep["codes"]
        ok = {0: "ok", None: "not run"}
        L.append("- tools: " + ", ".join(f"{k} {ok.get(v, 'failed')}" for k, v in c.items()) +
                 f"; frontend for formal/CDC: {rep.get('frontend') or 'none'}")
    for k, errs in (rep.get("errors") or {}).items():
        L.append(f"- first errors of {k}: " + "; ".join(f"`{e[:160]}`" for e in errs))
    L.append("")
    if rep["ports"]:
        L += ["## Ports of the top", "", "| Port | Direction | Kind | Width | Type | Handling |", "|---|---|---|---|---|---|"]
        for p in rep["ports"]:
            L.append(f"| {p['name']} | {p['direction']} | {p['kind']} | {p.get('width')} | {p.get('type') or ''} | "
                     f"{port_handling(p)} |")
        L.append("")
    if rep["parameters"]:
        L += ["Parameters: " + ", ".join(f"{p['name']}={p['value']}" for p in rep["parameters"]), ""]
    s = rep.get("structure")
    if s and not s.get("error"):
        L += ["## Structure (flattened netlist)", "",
              f"- flop bits: {s['flop_bits']}, latch bits: {s['latches']}, memories: {s['memories']}, "
              f"tri-state: {'yes' if s['tristate'] else 'no'}",
              "- clocks: " + (", ".join(f"`{k}` ({v['bits']} bits, {'/'.join(v['edges'])})" for k, v in
                                        s["clocks"].items()) or "none"),
              "- asynchronous resets: " + (", ".join(f"`{k}` (active {'/'.join(v['active'])})" for k, v in
                                                     s["async_resets"].items()) or "none"),
              "- synchronous resets: " + (", ".join(f"`{k}` (active {'/'.join(v['active'])})" for k, v in
                                                    s["sync_resets"].items()) or "none"), ""]
    L += ["## Stages", "", "| Stage | |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rep["stages"].items()]
    if rep.get("spec"):
        sp = rep["spec"]
        L += ["", "## Specification", "", f"`{Path(sp['file']).name}`: {sp.get('sections')} sections, "
              f"{sp['ports']} ports, {sp['parameters']} parameters, {sp['requirements']} requirement IDs, "
              f"{sp.get('normative')} normative sentences", ""]
        L += [f"- {f['severity']}: {f['message']}" for f in sp.get("findings", [])]
    return "\n".join(L) + "\n"
