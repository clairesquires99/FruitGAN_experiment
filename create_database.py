import sqlite3

conn = sqlite3.connect('experiment.db') 
c = conn.cursor()

c.execute('''
          CREATE TABLE results (
            [pk] INTEGER PRIMARY KEY,
            [session_id] VARCHAR(8),
            [target_category] VARCHAR(20),
            [iteration_num] INTEGER,
            [image] BLOB
          )
          ''')
                     
conn.commit()