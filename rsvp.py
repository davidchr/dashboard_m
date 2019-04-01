import sqlite3
import requests
import json
import datetime

conn = sqlite3.connect('meetup.db')
c = conn.cursor()

r = requests.get('http://stream.meetup.com/2/rsvps', stream=True)
for raw_rsvp in r.iter_lines():
    if raw_rsvp:
        rsvp = json.loads(raw_rsvp)
        for topic in rsvp["group"]["group_topics"]:
            c.execute("INSERT INTO rsvp VALUES (?, ?, ?, ?)", (topic["topic_name"], topic["urlkey"], rsvp["response"], datetime.datetime.now()))
            conn.commit()


conn.commit()
conn.close()