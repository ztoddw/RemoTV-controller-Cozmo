
import sqlite3 as sl
import time
#import sys

print(time.strftime('%x'), time.strftime('%H'))
#sys.exit()

conn = sl.connect('CozData.db', detect_types=sl.PARSE_COLNAMES)
conn.row_factory = sl.Row

"""
d=[[1,"abc"], [2,"def"]]
conn.execute("drop table jokes")    
conn.execute('create table jokes (jokeID int, jokeText text)')  # STRICT')
    # the strict keyword is available in SQLLite vers 3.37.0
conn.executemany("insert into jokes (jokeID, jokeText) values (?, ?)", d)
"""


#res = conn.execute('''select * 
#    from userCmdHistory where user="Religue" order by user,cmdDate''')  # where user="" #hour=5'):

#res = conn.execute('select * from sqlite_master')

res = conn.execute('''select *, round(numWords / dur, 2) as wordsPerSecond 
    from jokeDurations order by jokeID''')


rows = res.fetchall()
rows.insert(0, rows[0].keys())
maxLens = [0] * len(rows[0]) 
for row in rows:
    maxLens = [max(maxLens[i],len(str(row[i]))) for i in range(len(row))]

for row in rows:
    s=""
    for i in range(len(row)):
        s += str(row[i]).center(maxLens[i]+2)
    print(s)

"""
conn.execute('alter table userCmdHistory add column earliestTime time')
conn.execute('alter table userCmdHistory add column latestTime time')
conn.execute('alter table userCmdHistory add column activity text')
"""

conn.commit()
conn.close()
