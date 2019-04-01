import sqlite3

conn = sqlite3.connect("meetup.db")
c = conn.cursor()

c.execute("CREATE TABLE rsvp (topic_name text, urlkey text, response text, date text)")

conn.commit()

conn.close()