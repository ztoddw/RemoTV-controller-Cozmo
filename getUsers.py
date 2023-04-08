
#import json

import sqlite3 as sl
import time
import sys

print(time.strftime('%x'), time.strftime('%H:%M:%S'))
#sys.exit()

conn = sl.connect('CozData.db', detect_types=sl.PARSE_COLNAMES)
conn.row_factory = sl.Row

#conn.execute("drop table userCmdHistory")  #No, don't do this!

"""
if conn.execute("SELECT name FROM sqlite_master WHERE name='userCmdHistory'").fetchone() is None:
    conn.execute('create table userCmdHistory (cmdDate date, user text, hour int, cmd text, num int)')  # STRICT')
        # the strict keyword is available in SQLLite vers 3.37.0
        # I got syntax error, so I guess this python version has older SQLLite
"""

#conn.execute("""create unique index if not exists indexUserCmdHistory on userCmdHistory 
#    (cmdDate, user, hour, cmd)""")


def Upsert(vDate, vUser, vHour, vCmd, val):
    global conn
    conn.execute("""insert into userCmdHistory (cmdDate, user, hour, cmd, num) values ('{}','{}',{},'{}',{})
        on conflict (cmdDate, user, hour, cmd) do update set num = {}""".format(vDate,vUser,vHour,vCmd,val,val))

    conn.commit()


#conn.execute("delete from userCmdHistory")     #No, don't do this!
#conn.execute("delete from userCmdHistory where user like 'user%'")
#conn.commit


             # can a multiline string can be used as multine comment? yeah, but maybe it was doing something funny
"""
print ('Before:')
for res in conn.execute('select * from userCmdHistory'): # where hour=5'):
    print(res)

#Upsert('3/4/23', 'user1', 6, 'w', 3)
#Upsert('3/4/23', 'user1', 6, 'a', 3)
#Upsert('3/4/23', 'user1', 7, 'w', 4)
#conn.commit()

#print(4/0)  #Check if fatal error will rollback changes committed but conn not closed- nope, they are saved!

#Upsert('3/4/23', 'user1', 6, 'a', 4)
#Upsert(time.strftime('%x'), 'user2', time.strftime('%H'), 'w', 5)

#for res in conn.execute("SELECT * FROM sqlite_master"):

"""

#print ('After:')

# Example taken from https://www.sqlite.org/windowfunctions.html#udfwinfunc     vers 2.7
class WindowCombineActivity:
    t1 = str.maketrans('-X','01')
    t2 = str.maketrans('01','-X')
    
    def __init__(self):
        self.act = None 

    def step(self, value):
        """Add a row to the current window."""
        c = WindowCombineActivity   #to reference class vars
        if self.act is None and value != None : 
            self.act = value.ljust(30, '-')     # pad dashes on the right
        elif value != None :
            #print('')
            #print (self.act, value)
            #print (self.act.translate(c.t1), value.translate(c.t1))
            self.act = bin(int(self.act.translate(c.t1), 2) | int(value.ljust(30, '-').translate(c.t1), 2))[2:] \
                .translate(c.t2).rjust(30, '-')     # pad dashes on the left after OR'ing and trxlating back again.
            #maxlen = max(len(self.act), len(value))
            #print(len(self.act), maxlen)
            #print (self.act)

    def finalize(self):
        """Return the final value of the aggregate."""
        if self.act != None : 
            #print('final: ', self.act)
            return self.act


#w = WindowCombineActivity()
#w.step('--------------------X')
#w.step('-----------------X')
#print('testing: ', w.finalize())

conn.create_aggregate("combineAct", 1, WindowCombineActivity)

if len(sys.argv) > 1 and sys.argv[1]=='d' :
    res = conn.execute("""
    select * from (
        select *, row_number() over (order by cmdDate desc, hour desc, user, cmd) as rn
        from userCmdHistory a 
    ) qry where rn <= 25  order by rn
    """)

elif len(sys.argv) > 1 and sys.argv[1]=='u' :
    res = conn.execute("""
    select * from (
        select --, ifnull(length(activity),0) as lenAct 
          cmdDate, user, hour, group_concat(cmd,', ') as cmds
        , sum(num) as num, min(earliestTime) as earliestTime, max(latestTime) as latestTime
        , combineAct(activity) as activity
        , row_number() over (order by cmdDate desc, hour desc, user) as rn
        from userCmdHistory a   group by cmdDate, user, hour
    ) qry where rn <= 15  order by rn
    """)
else :
    res = conn.execute("""
    select * from (
        select /**/ a.user, min(a.cmdDate) as dateMin, b.dateMax
        , max(case when a.cmdDate=b.dateMax then a.hour end) as lastHour
        , count(distinct a.cmdDate) as numDays
        , min(a.hour) as hourMin, max(a.hour) as hourMax, count(distinct a.hour+a.cmdDate) as numHours
        , count(distinct a.cmd) as numUniqueCmds, sum(a.num) as totalCmds
        , sum(case when a.cmdDate=b.dateMax then a.num end) as cmdsLastDay
        , sum(case when lower(a.cmd)='j' then a.num end) as numCmdJ
        , sum(case when lower(a.cmd)='g' then a.num end) as numCmdG
        , sum(case when lower(a.cmd)='n' then a.num end) as numCmdN
        , rank() over (order by b.dateMax desc) as rankNum /**/
        from userCmdHistory a join (select b.user, max(b.cmdDate) as dateMax from userCmdHistory b
            group by b.user) b on b.user=a.user
        group by a.user, b.dateMax 
    ) where rankNum <= 15
    order by dateMax, lastHour, cmdsLastDay
    --order by cmdDate, hour, user, cmd
    """)


rows = res.fetchall()
rows.insert(0, rows[0].keys())  # Insert column names as first row.
maxLens = [0] * len(rows[0])    # Initialize list with length = # of columns.
for row in rows:                # Loop thru the row and columns to find max length of call columns.
    maxLens = [max(maxLens[i], len(str(row[i]))) for i in range(len(row))]

for row in rows:                # Loop thru the rows again to print the data.
    s=""
    for i in range(len(row)):   # Loop thru the columns and center the value for each field, leaving a space on each side.
        s += str(row[i]).center(maxLens[i]+2)
    print(s)


#print([column[0] for column in res.description])
#for row in res:
#    print(row)


conn.commit()
conn.close()



    # store as a dictionary? nah.
#userCmdHistory = {
#  'cmdDate':'2023-03-04'
#, 'users': {
#      'user':'user1'
#    , 'hours': {
#          'hour': 8
#        , 'commands': ['w',30,'s',30]
#      }
#  }
#}

          
#with open('test.txt','r',encoding='utf-8'):

