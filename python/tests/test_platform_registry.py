import unittest

from platforms import create_adapter


class PlatformRegistryTests(unittest.TestCase):
    def test_every_catalog_platform_can_be_created_offline(self):
        from platforms import PLATFORM_CATALOG
        for platform in PLATFORM_CATALOG:
            with self.subTest(platform=platform):
                self.assertEqual(create_adapter(platform, offline=True).capabilities.name, platform)

    def test_live_adapter_without_credentials_is_explicit(self):
        with self.assertRaises(ValueError):
            create_adapter("mastodon")


if __name__ == "__main__":
    unittest.main()
