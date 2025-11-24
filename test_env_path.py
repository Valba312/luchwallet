from dotenv import find_dotenv, load_dotenv
import os

env_path = find_dotenv()
print("Найденный .env:", env_path)

load_dotenv(env_path)

print("BOT_TOKEN:", os.getenv("BOT_TOKEN"))
