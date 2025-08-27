import logging
import shutil

from helpers.instadownloader import InstaDownloader
from helpers.mealie_api import MealieAPI
from helpers.config import load_config
from flask import Flask, jsonify, request, render_template


def create_app(config):
    mealie_api = MealieAPI(config["MEALIE_URL"], config["MEALIE_API_KEY"])
    downloader = InstaDownloader()
    app = Flask(__name__)
    print("Started succesfully")

    def execute_download(url):
        filepath = None

        try:
            post = downloader.download_instagram_post(url)
            filepath = "downloads/" + post.shortcode + "/"

            recipe_slug = mealie_api.create_recipe_from_html(post.caption)

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
        
    def execute_download_and_render_view(url):
        recipe_slug, error = execute_download(url)

        return render_template("index.html", successful=recipe_slug, error=error)
    
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            url = request.form.get("url")
            return execute_download_and_render_view(url)

        elif request.args.get('url') is not None and request.args.get('url') != "":
            url = request.args.get('url')
            return execute_download_and_render_view(url)

        return render_template("index.html")

    @app.route("/api", methods=["POST"])
    def api():
        url = None

        # POST request body has priority over query parameters
        request_json = request.get_json(force=True, silent=True)
        if request_json:
            url = request_json.get('url')
        # If there is no URL in POST request body, check query parameters
        if not url:
            url = request.args.get('url')

        if not url:
            return jsonify({"error": "URL was not provided. Please inform the url as query parameter or in the JSON body."}), 400
        
        recipe_slug, error = execute_download(url)

        return jsonify({
            "recipe_slug": recipe_slug,
            "error": error if error else None,
            "url": url
        })

    return app


if __name__ == "__main__":
    from waitress import serve

    config = load_config()
    app = create_app(config)
    serve(app, host="0.0.0.0", port=config["HTTP_PORT"])
