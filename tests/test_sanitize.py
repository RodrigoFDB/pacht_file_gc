import unittest

from modules.sanitize import sanitize_text


class SanitizeTests(unittest.TestCase):
    def test_sanitize_removes_invisible_and_tabs_and_trailing_spaces(self) -> None:
        config = {
            "remove_invisible_characters": True,
            "convert_tabs_to_spaces": True,
            "trim_trailing_spaces": True,
            "line_ending": "LF",
            "tab_size": 2,
        }
        content = "\ufeffa\tb  \r\nc\u200B\r\n"
        result = sanitize_text(content, config)
        self.assertTrue(result.changed)
        self.assertEqual(result.text, "a  b\nc\n")
        self.assertIn("removed_invisible_characters", result.actions)
        self.assertIn("tabs_to_spaces", result.actions)
        self.assertIn("trimmed_trailing_spaces", result.actions)
        self.assertIn("normalized_line_endings", result.actions)


if __name__ == "__main__":
    unittest.main()

