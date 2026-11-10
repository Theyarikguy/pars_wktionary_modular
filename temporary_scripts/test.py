import os
from pathlib import Path

import database.config as cfg
from database.config import settings
from database.connection import engine

print("cwd:              ", os.getcwd())
print("config file:      ", cfg.__file__)
print("settings type:    ", type(settings).__name__)
print("settings.URL:     ", settings.DATABASE_URL)
print("engine.url:       ", engine.url)
print("engine db path:   ", engine.url.database)
if engine.url.database:
    print("resolved path:    ", Path(engine.url.database).resolve())
    print("exists:           ", Path(engine.url.database).exists())