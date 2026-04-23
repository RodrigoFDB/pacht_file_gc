import unittest
import re

from modules.split_strings import split_long_strings


class SplitStringTests(unittest.TestCase):
    def test_split_long_strings_on_single_line(self) -> None:
        text = 'x = "abcdefghijklmnopqrstuvwxyz"\n'
        result = split_long_strings(text, max_length=10, chunk_size=5)
        self.assertTrue(result.changed)
        self.assertEqual(result.split_count, 1)
        self.assertEqual(result.text, 'x = "abcde" + "fghij" + "klmno" + "pqrst" + "uvwxy" + "z"\n')

    def test_split_preserves_escape_sequences(self) -> None:
        text = r'x = "aaaa\\nbbbb\\ncccc\\ndddd"' + "\n"
        result = split_long_strings(text, max_length=8, chunk_size=8)
        self.assertTrue(result.changed)
        parts = re.findall(r'"([^"]*)"', result.text)
        self.assertGreater(len(parts), 1)
        for part in parts[:-1]:
            trailing_slashes = len(part) - len(part.rstrip("\\"))
            self.assertEqual(trailing_slashes % 2, 0)


if __name__ == "__main__":
    unittest.main()
