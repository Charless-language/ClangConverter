import unittest
import sys
import os

# ClangConverterディレクトリをパスに追加してインポートできるようにする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from c2charless import C2Charless

class TestC2Charless(unittest.TestCase):
    def setUp(self):
        self.c2 = C2Charless()

    def test_tokenize_basic(self):
        code = "int x = 5;"
        self.c2.tokenize(code)
        tokens = self.c2.tokens
        # Expected: int, x, =, 5, ;, EOF
        self.assertEqual(tokens[0], ('KEYWORD', 'int'))
        self.assertEqual(tokens[1], ('ID', 'x'))
        self.assertEqual(tokens[2], ('OP', '='))
        self.assertEqual(tokens[3], ('NUMBER', '5'))
        self.assertEqual(tokens[4], ('OP', ';'))
        self.assertEqual(tokens[-1], ('EOF', 'EOF'))

    def test_transpile_simple_assignment(self):
        # int x = 10;
        code = "int x = 10;"
        self.c2.transpile(code)
        # 10 is pushed(500), stored(510) to addr 0
        # Output should contain raw opcodes.
        # Check generated output roughly
        self.assertTrue(len(self.c2.output) > 0)
        # Find PUSH 10
        found_push = False
        for item in self.c2.output:
            if isinstance(item, str) and "500" in item and "10" in item:
                 found_push = True
                 break
        self.assertTrue(found_push, "PUSH instruction for 10 not found")

    def test_resolve_labels(self):
        # while(1) { }
        # Should generate jumps
        code = "while(1) { }"
        self.c2.transpile(code)
        res = self.c2.resolve()
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)
        # Should contain jump opcode 700 or 701/702
        self.assertTrue("700" in res or "701" in res)

    def test_printf(self):
        code = 'printf("A");'
        self.c2.transpile(code)
        res = self.c2.resolve()
        # printf with string only -> 010 (PRINT_STR)
        self.assertTrue("010" in res)

if __name__ == '__main__':
    unittest.main()
