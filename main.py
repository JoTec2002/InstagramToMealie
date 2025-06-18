import os
import shutil

from helpers.instadownloader import InstaDownloader
from helpers.mealie_api import MealieAPI
from helpers.config import load_config
from flask import Flask, request, render_template

def create_app(config):
    mealie_api = MealieAPI(config["MEALIE_URL"], config["MEALIE_API_KEY"])
    downloader = InstaDownloader()
    app = Flask(__name__)
    print("Started succesfully")

    def execute_download(url):
        post = downloader.download_instagram_post(url)
        filepath = "downloads/" + post.shortcode + "/"

        try:
            recipe_slug = mealie_api.create_recipe_from_html(post.caption)

            mealie_api.update_recipe_orig_url(recipe_slug, url)
            image_file = filepath + post.date.strftime(format="%Y-%m-%d_%H-%M-%S_UTC") + ".jpg"
            mealie_api.upload_recipe_image(recipe_slug, image_file)
            if post.is_video:
                video_file = filepath + post.date.strftime(format="%Y-%m-%d_%H-%M-%S_UTC") + ".mp4"
                mealie_api.upload_recipe_asset(recipe_slug, video_file)

            shutil.rmtree(filepath)

            return render_template("index.html", successful="true")

        except Exception as e:
            shutil.rmtree(filepath)
            return repr(e)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            url = request.form.get("url")
            return execute_download(url)

        elif request.args.get('url') is not None and request.args.get('url') != "":
            url = request.args.get('url')
            return execute_download(url)

        return render_template("index.html")

    return app


if __name__ == "__main__":
    from waitress import serve
    config = load_config()
    app = create_app(config)
    serve(app, host="0.0.0.0", port=config["HTTP_PORT"])
