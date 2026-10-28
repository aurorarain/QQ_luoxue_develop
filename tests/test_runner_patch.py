import importlib.util
import pathlib
import unittest

p=pathlib.Path(__file__).resolve().parents[1]/'scripts/fix_runner_empty_tools.py'
spec=importlib.util.spec_from_file_location('runner_patch',p)
patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)

class RunnerPatch(unittest.TestCase):
    def test_no_early_return_and_idempotent(self):
        source='def reset():\n'+patch.OLD+'        stats = 1\n'
        result=patch.patched(source)
        self.assertNotIn('return',result)
        self.assertEqual(result,patch.patched(result))

    def test_unknown_version_rejected(self):
        with self.assertRaises(RuntimeError):patch.patched('unknown = True')
