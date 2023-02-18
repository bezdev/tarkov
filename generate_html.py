import os

from peewee import *
from playhouse.sqlite_ext import *

DATABASE = "tarkov.db"
db = SqliteDatabase(DATABASE)

class Quest(Model):
    name = CharField()
    url = CharField()
    trader = CharField()
    location = CharField()
    is_required_for_kappa = BooleanField()
    requirements = CharField()
    objectives = CharField()
    rewards = CharField()
    related_quests = JSONField()

    class Meta:
        database = db

db.connect()

quest_data = []
for quest in Quest.select():
    quest_data.append({"name": quest.name, "url": quest.url, "trader": quest.trader, "location": quest.location, "is_required_for_kappa": "true" if quest.is_required_for_kappa else "false"})

db.close()

try:
    os.remove("quests.html")
except OSError:
    pass

out_file = open("quests.html", "w")
base_file = open("quests_base.html", "r")
for line in base_file.readlines():
    out_file.write(f"{line}")
    if "quest data" in line:
        out_file.write("var QUEST_DATA = [\n")
        for quest in quest_data:
            out_file.write(f"    {str(quest)},\n")
        out_file.write("];\n")
base_file.close()
out_file.close()
