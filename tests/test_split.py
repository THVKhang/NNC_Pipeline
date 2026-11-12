"""Split test generation: grouping, validation, error routing, library shipped with the tests."""
import tempfile
import unittest
from pathlib import Path

from nnc import gen_tests, sim

LIB = '''"""API: Driver(dut).write(addr, data) -> None"""
from nnc_cocotb import *

class Driver:
    pass
'''
GROUP = '''from tb_demo import *
import cocotb

@cocotb.test()
async def test_chk_002_write(dut):
    """CHK-002: a write"""
    pass
'''


class SplitTest(unittest.TestCase):
    def test_groups(self):
        checks = [{"id": f"CHK-{i:03d}", "kind": "test", "group": "a" if i < 7 else "b"} for i in range(1, 10)]
        checks.append({"id": "CHK-099", "kind": "assertion", "group": "a"})
        gs = gen_tests.groups({"checks": checks}, size=5)
        self.assertEqual([len(g) for g in gs], [5, 4])      # the lone CHK-006 joins the next group
        self.assertEqual(sorted(c["id"] for g in gs for c in g), [f"CHK-{i:03d}" for i in range(1, 10)])

    def test_validate_library(self):
        self.assertEqual(gen_tests.validate_library(LIB), [])
        bad = LIB + "\n@cocotb.test()\nasync def test_x(dut):\n    pass\n"
        self.assertTrue(any("must not contain" in p for p in gen_tests.validate_library(bad)))
        self.assertTrue(any("docstring" in p for p in gen_tests.validate_library("from nnc_cocotb import *\n")))

    def test_validate_group(self):
        c2 = [{"id": "CHK-002"}]
        self.assertEqual(gen_tests.validate_group(GROUP, c2, "tb_demo", False), [])
        probs = gen_tests.validate_group(GROUP, c2 + [{"id": "CHK-003"}], "tb_demo", True)
        self.assertTrue(any("CHK-003" in p for p in probs))
        self.assertTrue(any("test_regression_random" in p for p in probs))
        self.assertTrue(any("import the library" in p
                            for p in gen_tests.validate_group(GROUP.replace("tb_demo", "x"), c2, "tb_demo", False)))

    def test_error_module(self):
        owner = {"test_chk_002_write": "test_demo_g1.py"}
        lib_tb = {"name": "test_chk_002_write", "traceback": 'File "/x/test_demo_g1.py", line 3\nFile "/x/tb_demo.py", line 9'}
        own_tb = {"name": "test_chk_002_write", "traceback": 'File "/x/tb_demo.py", line 9\nFile "/x/test_demo_g1.py", line 3'}
        self.assertEqual(gen_tests.error_module(lib_tb, owner, "tb_demo.py"), "tb_demo.py")
        self.assertEqual(gen_tests.error_module(own_tb, owner, "tb_demo.py"), "test_demo_g1.py")

    def test_library_shipped_with_tests(self):
        contract = {"top": "m", "interface": {"clock": "clk", "reset": {"name": "rst_n", "active_low": True},
                                              "parameters": [], "ports": []}}
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "tb_demo.py").write_text(LIB)
            (t / "test_demo_g1.py").write_text(GROUP)
            files = sim.build_inputs(contract, [], [], [t / "test_demo_g1.py"], {})
        self.assertIn("tb_demo.py", files)
        self.assertIn("COCOTB_TEST_MODULES = test_demo_g1\n", files["Makefile"])


if __name__ == "__main__":
    unittest.main()
