import os

os.environ["MINIFLOW_DOTENV"] = "0"  # tests never read the real .env (it may hold API keys)
