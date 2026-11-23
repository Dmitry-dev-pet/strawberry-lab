"""Independent input-boundary regressions for portable saved-scene QA."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from strawberry_generator.sdf.qa_inputs import parse_qa_inputs


class SdfQaInputsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source = root / 'inputs' / 'seed101.blend'
        self.scene = root / 'output' / 'sdf.blend'
        self.receipt = root / 'qa' / 'result.json'
        for p in (self.source, self.scene):
            p.parent.mkdir(parents=True, exist_ok=True)
        self.source.write_bytes(b'original-source')
        self.scene.write_bytes(b'sdf-result')
        self.pin = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def argv(self):
        return [str(self.scene), str(self.receipt), '--source', str(self.source)]

    def test_explicit_source_is_required_and_paths_can_be_anywhere(self):
        p, out, source = parse_qa_inputs(self.argv(), self.pin)
        self.assertEqual((p, out, source), (self.scene, self.receipt, self.source))
        with self.assertRaises(SystemExit):
            parse_qa_inputs([str(self.scene), str(self.receipt)], self.pin)

    def test_source_sha_is_verified_before_scene_evaluation(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            parse_qa_inputs(self.argv(), '0' * 64)

    def test_missing_inputs_fail_closed(self):
        self.source.unlink()
        with self.assertRaises(FileNotFoundError):
            parse_qa_inputs(self.argv(), self.pin)
        self.source.write_bytes(b'original-source')
        self.scene.unlink()
        with self.assertRaises(FileNotFoundError):
            parse_qa_inputs(self.argv(), self.pin)

    def test_cannot_overwrite_prior_receipt(self):
        self.receipt.parent.mkdir(parents=True)
        self.receipt.write_text('prior-evidence')
        with self.assertRaises(FileExistsError):
            parse_qa_inputs(self.argv(), self.pin)
        self.assertEqual(self.receipt.read_text(), 'prior-evidence')

    def test_source_and_output_cannot_alias(self):
        argv = [str(self.source), str(self.receipt), '--source', str(self.source)]
        with self.assertRaisesRegex(ValueError, 'different files'):
            parse_qa_inputs(argv, self.pin)


if __name__ == '__main__':
    unittest.main()
