import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from helpers.mealie_api import MealieAPI


class UploadRecipeAssetTest(unittest.TestCase):
    def setUp(self):
        self.api = MealieAPI.__new__(MealieAPI)
        self.api.MEALIE_URL = "http://mealie:9000"
        self.api.HEADERS = {"Authorization": "Bearer test"}

        asset = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        asset.close()
        self.asset_path = asset.name
        self.addCleanup(os.unlink, self.asset_path)

    @patch("helpers.mealie_api.requests.post")
    def test_skips_mp4_when_mealie_rejects_the_extension(self, post):
        post.return_value = Mock(
            status_code=400,
            text='{"detail":"Unsupported file extension"}',
        )
        post.return_value.json.return_value = {"detail": "Unsupported file extension"}

        result = self.api.upload_recipe_asset("recipe", self.asset_path)

        self.assertEqual(result, "")
        self.assertTrue(post.call_args.kwargs["files"]["file"].closed)

    @patch("helpers.mealie_api.requests.post")
    def test_keeps_other_asset_errors_fatal(self, post):
        post.return_value = Mock(status_code=400, text='{"detail":"Invalid request"}')
        post.return_value.json.return_value = {"detail": "Invalid request"}

        with self.assertRaisesRegex(Exception, "Status Code: 400"):
            self.api.upload_recipe_asset("recipe", self.asset_path)

    @patch("helpers.mealie_api.requests.post")
    def test_returns_mealie_response_after_successful_upload(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"id": "asset-id"}

        result = self.api.upload_recipe_asset("recipe", self.asset_path)

        self.assertEqual(result, {"id": "asset-id"})


if __name__ == "__main__":
    unittest.main()
