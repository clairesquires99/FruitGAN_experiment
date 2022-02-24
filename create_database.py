import sqlite3

conn = sqlite3.connect('flask-app/experiment.db') 
c = conn.cursor()
with open('database_schema.sql', 'r') as sql_file:
  conn.executescript(sql_file.read())
conn.commit()

conn.close()