import re
import unittest
from pathlib import Path

from check_setup import REQUIRED
from platforms.catalog import PLATFORM_CATALOG


class SetupConfigurationTests(unittest.TestCase):
    def test_every_catalog_platform_has_preflight_requirements(self):
        self.assertEqual(set(REQUIRED), set(PLATFORM_CATALOG))

    def test_env_example_declares_all_required_variables(self):
        env_example = (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")
        declared = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", env_example, re.MULTILINE))
        missing = sorted({name for names in REQUIRED.values() for name in names} - declared)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
