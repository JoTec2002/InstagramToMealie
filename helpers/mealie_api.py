import os

import requests


class MealieAPI:
    def __init__(self, url, key):
        self.MEALIE_URL = url.rstrip('/')
        self.API_KEY = key
        self.HEADERS = {
            "Authorization": f"Bearer {self.API_KEY}",
        }

    def get_user_self(self) -> dict:
        # Raises requests.HTTPError on a non-2xx answer, e.g. 401 for an invalid API key
        response = requests.get(f"{self.MEALIE_URL}/api/users/self", headers=self.HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

    def __get_recipe(self, recipe_id) -> dict:
        response = requests.get(f"{self.MEALIE_URL}/api/recipes/{recipe_id}", headers=self.HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Error while getting recipe from API! - Status Code: {response.status_code} - Response: {response.text}")

    def __put_recipe(self, recipe_id, data) -> str:
        response = requests.put(f"{self.MEALIE_URL}/api/recipes/{recipe_id}", headers=self.HEADERS, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Error while getting recipe from API! - Status Code: {response.status_code} - Response: {response.text}")

    def create_recipe_from_html(self, html_content: str) -> str:
        include_tags = True
        if "MEALIE_USE_INSTAGRAM_TAGS" in os.environ:
            if os.environ.get("MEALIE_USE_INSTAGRAM_TAGS").lower() == "false":
                include_tags = False

        recipe_data = {
            "includeTags": include_tags,
            "data": html_content
        }

        response = requests.post(
            f"{self.MEALIE_URL}/api/recipes/create/html-or-json",
            json=recipe_data,
            headers=self.HEADERS,
            timeout=int(os.environ.get("MEALIE_OPENAI_REQUEST_TIMEOUT") or 60)
        )

        if response.status_code == 201:
            recipe = response.json()
            print(f"Created recipe with ID: {recipe}")
        else:
            raise Exception(
                f"Error while getting Recipe from API! - Status Code: {response.status_code} - Response: {response.text}")

        return recipe

    def update_recipe_orig_url(self, recipe_id, orig_url) -> str:
        recipe = self.__get_recipe(recipe_id)
        recipe.update({"orgURL": orig_url})
        return self.__put_recipe(recipe_id, recipe)

    def upload_recipe_image(self, recipe_slug, image_url) -> str:
        files = {
            'image': open(image_url, 'rb')
        }
        data = {
            'extension': image_url.split('.')[-1]
        }
        response = requests.put(f"{self.MEALIE_URL}/api/recipes/{recipe_slug}/image", files=files, data=data,
                                headers=self.HEADERS)

        if response.status_code == 200:
            print(f"Added cover image")
            return response.json()
        else:
            raise Exception(
                f"Error while uploading Image to API! - Status Code: {response.status_code} - Response: {response.text}")

    def upload_recipe_asset(self, recipe_slug, recipe_asset) -> str:
        files = {
            'file': open(recipe_asset, 'rb')
        }
        data = {
            'extension': recipe_asset.split('.')[-1],
            'icon': "mdi-file-image",
            'name': recipe_slug + "_video"
        }
        response = requests.post(f"{self.MEALIE_URL}/api/recipes/{recipe_slug}/assets", files=files, data=data,
                                 headers=self.HEADERS)

        if response.status_code == 200:
            print(f"Added video asset")
            return response.json()
        else:
            raise Exception(
                f"Error while uploading Video Asset to API! - Status Code: {response.status_code} - Response: {response.text}")
