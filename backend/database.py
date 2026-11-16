

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Always load the .env file located beside this file.
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            f"DATABASE_URL is missing. Checked: {ENV_PATH}"
        )

    return psycopg.connect(database_url)
