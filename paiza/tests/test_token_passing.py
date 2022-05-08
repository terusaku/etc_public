import subprocess
from unittest import TestCase


class TestShuffle(TestCase):
    def _test_std(self, param):
        p = subprocess.Popen(
            ['python3', '2021_q3_token_passing.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = p.communicate(input=param[0].encode())

        self.assertEqual(err.decode(), '')
        self.assertEqual(out.decode().strip(), str(param[1]))

    
    def test_case(self):
        with open('./tests/data/token_passing_01_input', 'r') as f:
            in_01 = f.read()
        with open('./tests/data/token_passing_01_output', 'r') as f:
            out_01 = f.read()
        with open('./tests/data/token_passing_02_input', 'r') as f:
            in_02 = f.read()
        with open('./tests/data/token_passing_02_output', 'r') as f:
            out_02 = f.read()

        params = (
            (in_01, out_01),
            (in_02, out_02),
        )

        for param in params:
            with self.subTest(param=param):
                self._test_std(param)
