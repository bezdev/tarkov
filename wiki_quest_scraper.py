import os
import random
import requests
import time

from lxml import html
from peewee import *
from playhouse.sqlite_ext import *

DATABASE = "tarkov.db"
WIKI_BASE_PATH = "https://escapefromtarkov.fandom.com/"

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

def sleep_between_requests():
    offset = random.randint(50, 300)
    time.sleep(1 + offset / 1000)

def parse_quest(url):
    content = requests.get(url).content
    tree = html.fromstring(content)

    name = ""
    trader = ""
    location = ""
    is_required_for_kappa = ""
    requirements = ""
    objectives = ""
    rewards = ""
    previous_quests = []
    next_quests = []
    other_quests = []

    for el in tree.iter("h1"):
        if "class" in el.attrib and "page-header__title" in el.attrib["class"]:
            name = "".join(el.itertext()).strip()

    for el in tree.iter("h2"):
        text = "".join(el.itertext())
        if (text == "Requirements"):
            requirements = "".join(el.getnext().itertext())
        elif (text == "Objectives"):
            objectives = "".join(el.getnext().itertext())
        elif (text == "Rewards"):
            rewards = "".join(el.getnext().itertext())

    for el in tree.iter("td"):
        if "class" in el.attrib and "va-infobox-content" in el.attrib["class"]:
            if "".join(el.itertext()).startswith("Previous:"):
                for quest_link in el.iter("a"):
                    previous_quests.append(quest_link.attrib["href"])
            elif "".join(el.itertext()).startswith("Leads to:"):
                for quest_link in el.iter("a"):
                    next_quests.append(quest_link.attrib["href"])
            elif "".join(el.itertext()).startswith("Other choices:"):
                for quest_link in el.iter("a"):
                    other_quests.append(quest_link.attrib["href"])

    for el in tree.iter("td"):
        if "class" in el.attrib and "va-infobox-label" in el.attrib["class"]:
            if "given by" in "".join(el.itertext()).lower():
                trader = "".join(el.getnext().getnext().itertext())
            elif "location" in "".join(el.itertext()).lower():
                location = "".join(el.getnext().getnext().itertext())
            elif "kappa container" in "".join(el.itertext()).lower():
                is_required_for_kappa = "".join(el.getnext().getnext().itertext()).lower().startswith("yes")

    # print(name)
    # print(requirements)
    # print(objectives)
    # print(rewards)

    # print(trader)
    # print(location)
    # print(is_required_for_kappa)

    # print(previous_quests)
    # print(next_quests)
    # print(other_quests)

    q = Quest(
          name = name,
          url = url,
          trader = trader,
          location = location,
          is_required_for_kappa = is_required_for_kappa,
          requirements = requirements,
          objectives = objectives,
          rewards = rewards,
          related_quests = { "previous_quests": previous_quests, "next_quests": next_quests, "other_quests": other_quests })

    q.save()

def parse_quest_list(urls):
    QUEST_LIST_FILE_NAME = "quests.txt"

    quests = []
    for url in urls:
        content = requests.get(url).content
        tree = html.fromstring(content)
        for a in tree.findall('.//*[@id="mw-pages"]/div/div')[0].iter("a"):
            quests.append({ "name": a.text, "url": f"{WIKI_BASE_PATH}{a.attrib['href']}" })

        sleep_between_requests()

    try:
        os.remove(QUEST_LIST_FILE_NAME)
    except OSError:
        pass

    quest_urls = []
    # file = open(QUEST_LIST_FILE_NAME, "w")
    for quest in quests:
    #     file.write(f"{str(quest)},\n")
        quest_urls.append(quest["url"])
    # file.flush()
    # file.close()

    return quest_urls

# main
db.connect()
db.drop_tables([Quest])
db.create_tables([Quest])

quest_urls = parse_quest_list(["https://escapefromtarkov.fandom.com/wiki/Category:Quests", "https://escapefromtarkov.fandom.com/wiki/Category:Quests?pagefrom=Revision+-+Reserve#mw-pages"])
quest_scraped_count = 0
quest_count = len(quest_urls)
print(f"Scraping {quest_count} quests...")
for url in quest_urls:
    parse_quest(url)
    quest_scraped_count += 1

    print(f"Scraping {quest_scraped_count}/{quest_count} ({round(100.0 * quest_scraped_count / quest_count, 2)}%): {url}")

    sleep_between_requests()

db.close()
