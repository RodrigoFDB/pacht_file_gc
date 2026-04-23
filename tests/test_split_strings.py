import unittest

from modules.split_strings import split_long_strings


class SplitStringTests(unittest.TestCase):
    def test_split_long_strings_on_single_line(self) -> None:
        text = 'x = "abcdefghijklmnopqrstuvwxyz"\n'
        result = split_long_strings(text, max_length=10, chunk_size=5)
        self.assertTrue(result.changed)
        self.assertEqual(result.split_count, 1)
        self.assertEqual(result.text, 'x = "abcde" + "fghij" + "klmno" + "pqrst" + "uvwxy" + "z"\n')


if __name__ == "__main__":
    unittest.main()

