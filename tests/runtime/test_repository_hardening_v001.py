from __future__ import annotations

import unittest

from tools.check_repository_hygiene import check_repository


class RepositoryHardeningV001Tests(unittest.TestCase):
    def test_repository_hardening_contract(self) -> None:
        result = check_repository()
        self.assertTrue(result["ok"], result["failures"])
        self.assertEqual(result["version"], "0.0.1")
        self.assertEqual(result["channel"], "pre-release")
        self.assertEqual(result["checks"]["typescript"], "6.0.3")


if __name__ == "__main__":
    unittest.main()
