import os
import dotenv

def require(varname: str) -> str:
    val = os.getenv(varname)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {varname}")
    return val


def load_config() -> dict:
    dotenv.load_dotenv()

    config = {
        "MEALIE_URL": require("MEALIE_URL"),
        "MEALIE_API_KEY": require("MEALIE_API_KEY"),
        "INSTA_USER": require("INSTA_USER"),
        "INSTA_PWD": os.getenv("INSTA_PWD"),
        "INSTA_TOTP_SECRET": os.getenv("INSTA_TOTP_SECRET"),
        "MEALIE_OPENAI_REQUEST_TIMEOUT": int(os.getenv("MEALIE_OPENAI_REQUEST_TIMEOUT", "60")),
        "HTTP_PORT": int(os.getenv("HTTP_PORT", "9001")),
    }

    if not os.path.isfile("./session-file") and not config["INSTA_PWD"]:
        raise RuntimeError("Must provide session-file or INSTA_PWD in environment")

    return config
