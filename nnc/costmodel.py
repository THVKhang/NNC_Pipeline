"""Agent cost of a run, estimated before any agent call (ROADMAP 26.1).

The estimate is fitted on what the committed designs cost (work/report.json, `agent_cost_usd.by_agent`, every
call of their history: re-runs and repairs included), against the size of their documents (the tokens of the
indexed rule documents):

    cost of the stages ≈ c · tokens^k       (least squares on the logarithms; k is about 0.7)

Each stage gets the median share of its agents in that cost, so a run that goes on from a later stage is given
only the stages it still runs. The range shown is half to twice the middle value; `holdout` in the model says
for how many designs the cost fell in that range when the design itself was left out of the fit. Cost depends
far less on size than on how much repair a design needs (failing tests, triage), so the range is wide and a
design can still cost more: the budget cap (`nnc run --max-cost`) is what bounds the spending.

Designs derived from another (`derived_from`, `nnc derive`) are left out: they reuse its verification, so their
agents are not those of a run of `nnc run`. Agents behind an option `nnc run` does not use (coverage closure
A10/A11, RTL generation A15, spec drafting A0, A16-A18) are not counted.

The committed model is nnc/data/cost_model.json; a unit test checks it equals the fit of the committed reports.
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "data" / "cost_model.json"
# the agents behind each stage of `nnc run` (A1 extract, A2 review, A3 open questions, A4 contract, A5 SVA,
# A6 cover points, A7 tests, A13 formal environment, A14 repair of the test infrastructure during sim,
# A9 triage, A12 mutation map)
STAGE_AGENTS = {"extract": ("A1",), "review": ("A2", "A3"), "contract": ("A4",), "gen-sva": ("A5", "A6"),
                "gen-tests": ("A7",), "gen-env": ("A13",), "sim": ("A14",), "triage": ("A9",), "mutate": ("A12",)}
RANGE = (0.5, 2.0)


def _tokens_of_indexes(paths) -> int:
    return sum(json.loads(Path(p).read_text(encoding="utf-8"))["stats"]["chars"] // 4 for p in paths)


def samples(designs_root: Path) -> list[dict]:
    """One sample per committed design that ran the flow on a given RTL: name, tokens, cost per stage."""
    from nnc.flow import index_path
    from nnc.project import Design, ProjectError
    out = []
    for root in sorted(Path(designs_root).iterdir()):
        rep = root / "work" / "report.json"
        if not rep.is_file():
            continue
        try:
            d = Design.open(root)
        except ProjectError:
            continue
        if d.config().get("derived_from"):   # reuses the verification of the design it derives from
            continue
        idx = [index_path(d, doc) for doc in d.rule_documents()]
        if not idx or not all(p.is_file() for p in idx):
            continue
        by = (json.loads(rep.read_text(encoding="utf-8")).get("agent_cost_usd") or {}).get("by_agent") or {}
        stages = {s: round(sum(by.get(a, 0.0) for a in ags), 4) for s, ags in STAGE_AGENTS.items()}
        if sum(stages.values()) <= 0:
            continue
        out.append({"design": root.name, "tokens": _tokens_of_indexes(idx), "stages": stages})
    return out


def _power_fit(points: list[tuple[float, float]]) -> tuple[float, float]:
    xs = [math.log(x) for x, _ in points]
    ys = [math.log(y) for _, y in points]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return math.exp(my - k * mx), k


def fit(samp: list[dict]) -> dict:
    pts = [(s["tokens"], sum(s["stages"].values())) for s in samp]
    c, k = _power_fit(pts)
    shares = {st: statistics.median(s["stages"][st] / sum(s["stages"].values()) for s in samp)
              for st in STAGE_AGENTS}
    norm = sum(shares.values())
    shares = {st: round(v / norm, 4) for st, v in shares.items()}
    held = []
    for i, s in enumerate(samp):
        ci, ki = _power_fit([p for j, p in enumerate(pts) if j != i])
        est = ci * s["tokens"] ** ki
        act = sum(s["stages"].values())
        held.append({"design": s["design"], "estimate": round(est, 2), "actual": round(act, 2),
                     "in_range": RANGE[0] * est <= act <= RANGE[1] * est})
    return {"c": round(c, 6), "k": round(k, 4), "shares": shares, "range": list(RANGE),
            "holdout": {"in_range": sum(h["in_range"] for h in held), "designs": len(held), "by_design": held},
            "samples": samp}


def load() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def write(designs_root: Path) -> dict:
    model = fit(samples(designs_root))
    MODEL_PATH.write_text(json.dumps(model, indent=1) + "\n", encoding="utf-8")
    return model


def estimate(tokens: int, stages=None, model: dict | None = None) -> dict:
    """{tokens, low, mid, high, by_stage} in USD for the given stages (default every stage of the flow)."""
    m = model or load()
    whole = m["c"] * max(int(tokens), 1) ** m["k"]
    names = [s for s in (stages if stages is not None else STAGE_AGENTS) if s in m["shares"]]
    by = {s: round(whole * m["shares"][s], 2) for s in names}
    mid = sum(whole * m["shares"][s] for s in names)
    lo, hi = m["range"]
    return {"tokens": int(tokens), "mid": round(mid, 2), "low": round(mid * lo, 2), "high": round(mid * hi, 2),
            "by_stage": by, "holdout": f"{m['holdout']['in_range']} of {m['holdout']['designs']}"}


def document_tokens(files) -> int:
    """Tokens of documents as the flow indexes them (no agent)."""
    from nnc.ingest import build_index
    return sum(build_index(Path(f))["stats"]["chars"] // 4 for f in files)


def text(est: dict) -> str:
    return (f"estimated agent cost {est['low']:.2f}-{est['high']:.2f} USD (middle {est['mid']:.2f}) for "
            f"{est['tokens']} document tokens; the range held for {est['holdout']} committed designs")
