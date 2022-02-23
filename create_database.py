import sqlite3

conn = sqlite3.connect('experiment.db') 
c = conn.cursor()

c.execute('''
          CREATE TABLE results (
            [session_id] VARCHAR(8) NOT NULL,
            [target_category] VARCHAR(20) NOT NULL,
            [iteration_num] INTEGER NOT NULL,
            [image] BLOB NOT NULL
          )
          ''')
                     
conn.commit()