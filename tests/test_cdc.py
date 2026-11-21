"""Structural CDC check (nnc/cdc.py) on hand-made Yosys netlists."""
import unittest

from nnc import cdc

# Bits: 2 clk_a, 3 clk_b, 4 rst_n, 5 x (domain A), 6 d_in (asynchronous)
CONTRACT = {"top": "m", "interface": {
    "clock_relation": "async",
    "clocks": [{"name": "clk_a", "domain": "A"}, {"name": "clk_b", "domain": "B"}],
    "resets": [{"name": "rst_n", "active_low": True, "clock": "clk_a"}],
    "ports": [{"name": "clk_a", "direction": "input", "domain": "A"},
              {"name": "clk_b", "direction": "input", "domain": "B"},
              {"name": "rst_n", "direction": "input", "domain": "A"},
              {"name": "x", "direction": "input", "domain": "A"},
              {"name": "d_in", "direction": "input", "domain": "ASYNC"},
              {"name": "o", "direction": "output", "domain": "B"}]}}


def ff(clk, d, q, arst=None):
    conn = {"CLK": [clk], "D": d, "Q": q}
    dirs = {"CLK": "input", "D": "input", "Q": "output"}
    if arst is not None:
        conn["ARST"] = [arst]
        dirs["ARST"] = "input"
    return {"type": "$adff" if arst is not None else "$dff", "connections": conn, "port_directions": dirs}


def gate(kind, ins: dict, out):
    conn = dict(ins)
    conn["Y"] = out
    return {"type": kind, "connections": conn,
            "port_directions": {**{k: "input" for k in ins}, "Y": "output"}}


def netlist(cells, nets):
    ports = {"clk_a": {"direction": "input", "bits": [2]}, "clk_b": {"direction": "input", "bits": [3]},
             "rst_n": {"direction": "input", "bits": [4]}, "x": {"direction": "input", "bits": [5]},
             "d_in": {"direction": "input", "bits": [6]}, "o": {"direction": "output", "bits": [99]}}
    return {"modules": {"m": {"attributes": {"top": "00000000000000000000000000000001"}, "ports": ports,
                              "cells": cells, "netnames": {k: {"bits": v} for k, v in nets.items()}}}}


class CdcTest(unittest.TestCase):
    def kinds(self, res):
        return {r["flop"]: r["kind"] for r in res["crossings"]}

    def test_classification(self):
        cells = {
            "a": ff(2, [5], [10], arst=4),                 # domain A register
            "s1": ff(3, [10], [11]), "s2": ff(3, [11], [12]),   # two-flop synchronizer into B
            "and": gate("$and", {"A": [10], "B": [12]}, [13]),
            "u": ff(3, [13], [14]),                        # A data through logic into B: UNSYNC
            "t1": ff(3, [6], [15]), "t2": ff(3, [15], [16]),    # async input, first stage also read
            "not": gate("$not", {"A": [15]}, [17]), "tu": ff(3, [17], [18]),
            "p": ff(2, [5], [20]),                         # payload in A
            "mux": gate("$mux", {"A": [21], "B": [20], "S": [12]}, [22]),
            "q": ff(3, [22], [21]),                        # payload captured under the synchronized flag
            "rb": ff(3, [12], [23], arst=4),               # B flop reset by the A-domain reset
        }
        nets = {"reg_a": [10], "sync1": [11], "sync2": [12], "bad": [14], "meta1": [15], "meta2": [16],
                "pay": [20], "cap": [21], "rb": [23]}
        res = cdc.analyse(netlist(cells, nets), CONTRACT)
        k = self.kinds(res)
        self.assertEqual(k["sync1"], "SYNC")
        self.assertEqual(k["bad"], "UNSYNC")
        self.assertEqual(k["meta1"], "FIRST_STAGE_READ")
        self.assertEqual(k["cap"], "QUALIFIED")
        sync = next(r for r in res["crossings"] if r["flop"] == "sync1")
        self.assertEqual(sync["stages"], 2)
        cap = next(r for r in res["crossings"] if r["flop"] == "cap")
        self.assertIn("sync2", cap["note"])
        self.assertEqual(res["resets"][0]["reset_from"], ["rst_n"])
        self.assertEqual(cdc.verdict([res]), "violations")

    def test_multibit_and_one_domain(self):
        cells = {"g": ff(2, [5, 5], [10, 11]),
                 "s1a": ff(3, [10], [12]), "s2a": ff(3, [12], [13]),
                 "s1b": ff(3, [11], [14]), "s2b": ff(3, [14], [15])}
        res = cdc.analyse(netlist(cells, {"gray": [10, 11], "ya": [12], "yb": [14]}), CONTRACT)
        self.assertEqual(set(self.kinds(res).values()), {"SYNC_MULTIBIT"})
        self.assertEqual(cdc.verdict([res]), "review")
        sync = dict(CONTRACT["interface"], clock_relation=None)
        res2 = cdc.analyse(netlist(cells, {"gray": [10, 11]}), {"top": "m", "interface": sync})
        self.assertEqual(res2["crossings"], [])                # synchronous clocks: one domain
        self.assertEqual(cdc.verdict([res2]), "clean")

    def test_conditional_async_inputs(self):
        self.assertEqual(cdc.async_inputs_for(["i_gpio:GpioAsyncOn=1", "rx"], {"GpioAsyncOn": 1}), ["i_gpio", "rx"])
        self.assertEqual(cdc.async_inputs_for(["i_gpio:GpioAsyncOn=1"], {"GpioAsyncOn": 0}), [])


if __name__ == "__main__":
    unittest.main()
