import logging
import shutil

import requests

from helpers.instadownloader import InstaDownloader
from helpers.mealie_api import MealieAPI
from helpers.config import load_config
from flask import Flask, jsonify, request, render_template


def create_app(config):
    # Without MEALIE_API_KEY, each request has to bring its own key (stored in the user's browser)
    server_mealie_api = None
    if config["MEALIE_API_KEY"]:
        server_mealie_api = MealieAPI(config["MEALIE_URL"], config["MEALIE_API_KEY"])
        check_mealie_connection(server_mealie_api)
    else:
        print("\nMEALIE_API_KEY not set, users must authenticate with their own Mealie API key")
    downloader = InstaDownloader()
    app = Flask(__name__)
    print("Started succesfully")

    def resolve_mealie_api(api_key=None):
        if server_mealie_api:
            return server_mealie_api

        if not api_key and request.authorization and request.authorization.type == "bearer":
            api_key = request.authorization.token
        if not api_key:
            return None

        return MealieAPI(config["MEALIE_URL"], api_key)

    def render_index(**context):
        return render_template("index.html", server_auth=server_mealie_api is not None, **context)

    def execute_download(mealie_api, url):
        filepath = None

        try:
            post = downloader.download_instagram_post(url)
            filepath = "downloads/" + post.shortcode + "/"

            post_caption = post.caption
            if not isinstance(post_caption, str):
                raise TypeError(f"Expected str, got {type(post_caption).__name__}, value: {post_caption}")
            recipe_slug = mealie_api.create_recipe_from_html(post_caption)

            mealie_api.update_recipe_orig_url(recipe_slug, url)
            image_file = filepath + post.date.strftime(format="%Y-%m-%d_%H-%M-%S_UTC") + ".jpg"
            mealie_api.upload_recipe_image(recipe_slug, image_file)
            if post.is_video:
                video_file = filepath + post.date.strftime(format="%Y-%m-%d_%H-%M-%S_UTC") + ".mp4"
                mealie_api.upload_recipe_asset(recipe_slug, video_file)

            shutil.rmtree(filepath)

            return recipe_slug, ""

        except Exception as e:
            logging.exception(f"Error downloading or processing Instagram post")
            if filepath:
                shutil.rmtree(filepath)
            return False, repr(e)

    @app.route("/", methods=["GET", "POST"])
    def index():
        url = request.form.get("url") if request.method == "POST" else request.args.get("url")
        if not url:
            return render_index()

        mealie_api = resolve_mealie_api(request.form.get("api_key"))
        if mealie_api is None:
            if request.method == "GET":
                # The API key lives in the browser, so the page submits the URL itself once it has loaded
                return render_index(url=url, auto_submit=True)
            return render_index(url=url, error="Not authenticated with Mealie. Please provide an API key.")

        recipe_slug, error = execute_download(mealie_api, url)

        return render_index(successful=recipe_slug, error=error)

    @app.route("/api/user", methods=["GET"])
    def user():
        mealie_api = resolve_mealie_api()
        if mealie_api is None:
            return jsonify({"error": "Mealie API key was not provided."}), 401

        try:
            mealie_user = mealie_api.get_user_self()
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return jsonify({"error": "Invalid Mealie API key."}), 401
            return jsonify({"error": f"Mealie responded with status code {e.response.status_code}."}), 502
        except requests.RequestException as e:
            logging.exception("Error connecting to Mealie")
            return jsonify({"error": f"Could not connect to Mealie: {e}"}), 502

        return jsonify({"username": mealie_user.get("username") or mealie_user.get("email")})

    @app.route("/api", methods=["POST"])
    def api():
        mealie_api = resolve_mealie_api()
        if mealie_api is None:
            return jsonify(
                {"error": "Mealie API key was not provided. Please inform it as 'Authorization: Bearer <key>' header."}), 401

        url = None

        # POST request body has priority over query parameters
        request_json = request.get_json(force=True, silent=True)
        if request_json:
            url = request_json.get('url')
        # If there is no URL in POST request body, check query parameters
        if not url:
            url = request.args.get('url')

        if not url:
            return jsonify(
                {"error": "URL was not provided. Please inform the url as query parameter or in the JSON body."}), 400

        recipe_slug, error = execute_download(mealie_api, url)

        return jsonify({
            "recipe_slug": recipe_slug,
            "error": error if error else None,
            "url": url
        })

    return app


def check_mealie_connection(mealie_api):
    print(f"\nChecking connection and validating auth data...")
    try:
        mealie_api.get_user_self()
        print(f"\nConnection established! Auth data validated!")
    except requests.RequestException as e:
        print(f"\nError while connecting to your Mealie API! - {e}")


if __name__ == "__main__":
    from waitress import serve

    config = load_config()
    app = create_app(config)
    serve(app, host="0.0.0.0", port=config["HTTP_PORT"])
