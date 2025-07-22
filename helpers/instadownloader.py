import pickle
import os
import re
import instaloader
import pyotp
from playwright import sync_api
from instaloader import Post, TwoFactorAuthRequiredException, BadCredentialsException

SESSION_FILE = "./session-file"


class InstaDownloader:
    def __init__(self):
        self._cookies = None
        self.loader = instaloader.Instaloader(download_comments=False,
                                              download_geotags=False,
                                              save_metadata=False,
                                              dirname_pattern="downloads/{target}", )
        try:
            user = os.environ.get('INSTA_USER')
            if os.path.isfile(SESSION_FILE):
                self.loader.load_session_from_file(user, SESSION_FILE)
            else:
                self.loader.login(os.environ.get("INSTA_USER"), os.environ.get("INSTA_PWD"))
        except TwoFactorAuthRequiredException:  # Probably not going to work https://github.com/instaloader/instaloader/issues/1217
            print(os.environ.get("INSTA_TOTP_SECRET"))
            totp = pyotp.TOTP(os.environ.get("INSTA_TOTP_SECRET"))
            print(totp.now())
            try:
                self.loader.two_factor_login(totp.now())
            except BadCredentialsException:
                self.loader.two_factor_login(totp.now())

        print(self.loader.test_login())

    def get_cookies(self) -> None:
        with open(SESSION_FILE, "rb") as f:
            cookies_dict = pickle.load(f)

        self._cookies = [
            {
                'name': name,
                'value': value,
                'domain': '.instagram.com',
                'path': '/',
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Lax',
            }
            for name, value in cookies_dict.items()
        ]

    def resolve_share_link(self, share_url) -> str:
        if not self._cookies:
            raise RuntimeError("Cookies not loaded")

        with sync_api.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(self._cookies)
            page = context.new_page()
            print(f"Visiting: {share_url}")
            page.goto(share_url, wait_until="domcontentloaded")
            final_url = page.url
            print(f"Resolved to: {final_url}")
            browser.close()
            return final_url

    def download_instagram_post(self, url) -> Post | None:
        # Check if we got a deep share link first
        if '/share/' in url:
            print("Got a deep share link, resolving...")
            self.get_cookies()
            resolved_url = self.resolve_share_link(url)
        else:
            resolved_url = url

        # Validate and extract shortcode from the URL
        match = re.search(r'(https?://)?(www\.)?instagram\.com/(p|reel|tv)/([A-Za-z0-9_-]+)', resolved_url)
        if not match:
            print(f"Received invalid Instagram URL ({resolved_url}). Please make sure it is a post, reel, or IGTV URL.")
            return None

        shortcode = match.group(4)  # Extract the shortcode from the URL

        try:
            # Load and download the post using the shortcode
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            self.loader.download_post(post, target=post.shortcode)
            print(f"Downloaded post: {resolved_url}")
            return post
        except Exception as e:
            print(f"Error downloading post: {e}")
