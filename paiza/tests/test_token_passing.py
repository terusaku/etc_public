import glob
import subprocess
from unittest import TestCase

import lizard


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


class TestLizard(TestCase):
    def lizard_targets(self):
        path = './*.py'
        files = glob.glob(path)
        return files

    def test_lizard(self):
        targets = self.lizard_targets()
        if not targets:
            assert True
        else:
            results = []
            for code in targets:
                analysis = lizard.analyze_file(code)
                for i in analysis.function_list:
                    result = {}
                    result['name'] = analysis.__dict__['filename'] + '.' + i.__dict__['name']
                    result['ccn'] = i.__dict__['cyclomatic_complexity'] 
                    result['nloc'] = i.__dict__['nloc']

                    assert result['ccn'] < 15 # cyclomatic complexity number
                    assert result['nloc'] < 50 # lines of code without comments
                    results.append(result)

            print(results)
