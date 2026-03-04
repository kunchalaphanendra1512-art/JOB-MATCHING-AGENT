import sqlite3, os
path=os.path.join('backend','hiresense.db')
print('exists', os.path.exists(path))
conn=sqlite3.connect(path)
print(list(conn.execute('SELECT id,title,poster_email FROM jobs')))
conn.close()