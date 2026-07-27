import unittest
from unittest.mock import Mock, patch

from helpers.instadownloader import InstaDownloader


class InstagramUrlTest(unittest.TestCase):
    def setUp(self):
        self.downloader = InstaDownloader.__new__(InstaDownloader)
        self.downloader.loader = Mock()
        self.post = Mock(shortcode="DbGWtcoIgQw")

    def assert_downloads_shortcode(self, url):
        with patch(
            "helpers.instadownloader.instaloader.Post.from_shortcode",
            return_value=self.post,
        ) as from_shortcode:
            result = self.downloader.download_instagram_post(url)

        self.assertIs(result, self.post)
        from_shortcode.assert_called_once_with(
            self.downloader.loader.context,
            "DbGWtcoIgQw",
        )
        self.downloader.loader.download_post.assert_called_once_with(
            self.post,
            target="DbGWtcoIgQw",
        )

    def test_accepts_singular_reel_url(self):
        self.assert_downloads_shortcode(
            "https://www.instagram.com/reel/DbGWtcoIgQw/"
        )

    def test_accepts_plural_reels_url(self):
        self.assert_downloads_shortcode(
            "https://www.instagram.com/reels/DbGWtcoIgQw/"
        )

    def test_rejects_invalid_instagram_url_with_clear_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "Expected a post, reel, reels, or IGTV URL",
        ):
            self.downloader.download_instagram_post(
                "https://www.instagram.com/explore/"
            )


if __name__ == "__main__":
    unittest.main()
