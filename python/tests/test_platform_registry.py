import unittest

from platforms import create_adapter


class PlatformRegistryTests(unittest.TestCase):
    def test_every_catalog_platform_can_be_created_offline(self):
        from platforms import PLATFORM_CATALOG
        for platform in PLATFORM_CATALOG:
            with self.subTest(platform=platform):
                self.assertEqual(create_adapter(platform, offline=True).capabilities.name, platform)

    def test_unverified_live_adapter_is_explicit(self):
        with self.assertRaises(NotImplementedError):
            create_adapter("mastodon")

    def test_only_declared_production_adapters_can_start_live(self):
        from platforms.catalog import PLATFORM_CATALOG, PRODUCTION_READY

        self.assertEqual([name for name, ready in PRODUCTION_READY.items() if ready], ["line"])
        for platform, ready in PRODUCTION_READY.items():
            if not ready:
                with self.subTest(platform=platform):
                    with self.assertRaises(NotImplementedError):
                        create_adapter(platform)


if __name__ == "__main__":
    unittest.main()
