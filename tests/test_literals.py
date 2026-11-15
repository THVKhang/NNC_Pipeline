"""Configuration awareness: run-set prompt text and hard-coded default values."""
import unittest

from nnc import literals

CONTRACT = {"top": "m", "interface": {"clock": "clk", "reset": {"name": "rst_n", "active_low": True}, "ports": [],
                                      "parameters": [{"name": "PARA_DEPTH", "default": "8"},
                                                     {"name": "PARA_W", "default": "32"},
                                                     {"name": "PARA_FIXED", "default": "16"}]}}
RUNS = [{"label": "base.s1", "config": "base", "params": {}, "opts": {"defines": [], "plusargs": ""}, "note": "CFG-BASE"},
        {"label": "small.s1", "config": "small", "params": {"PARA_DEPTH": 2, "PARA_W": 1},
         "opts": {"defines": ["SYN"], "plusargs": ""}, "clock_periods": {"clk": 7}}]


class LiteralsTest(unittest.TestCase):
    def test_config_text(self):
        t = literals.config_text(CONTRACT, RUNS)
        self.assertIn("base: default parameters  (CFG-BASE)", t)
        self.assertIn("small: PARA_DEPTH=2, PARA_W=1; defines SYN; clocks clk=7 ns", t)
        self.assertEqual(literals.config_text(CONTRACT, None), "")

    def test_varying_defaults(self):
        self.assertEqual(literals.varying_defaults(CONTRACT, RUNS), {8: ["PARA_DEPTH"], 32: ["PARA_W"]})

    def test_hardcoded_python(self):
        code = ('DEPTH = PARAMS.get("PARA_DEPTH", 8)\n'      # the parameter's own lookup: ignored
                "for i in range(8):\n"                        # flagged
                "    pass\n"
                "n = 8  # nnc-literal-ok: eight retries\n"    # kept on purpose
                "s = 'fill 8 words'\n"                        # inside a string: ignored
                "x = 16\n")                                   # PARA_FIXED does not change: ignored
        w = literals.hardcoded(code, CONTRACT, RUNS, "python")
        self.assertEqual(len(w), 1)
        self.assertIn("line 2: literal 8 equals the default of PARA_DEPTH", w[0])

    def test_hardcoded_sv(self):
        code = ("  localparam int D = PARA_DEPTH;\n"
                "  wire full = (cnt == 8);   // depth\n"
                "  wire [31:0] z = 32'h0;\n"
                "  // a comment with 32\n")
        w = literals.hardcoded(code, CONTRACT, RUNS, "sv")
        self.assertEqual([x.split(":")[0] for x in w], ["line 2"])


if __name__ == "__main__":
    unittest.main()
