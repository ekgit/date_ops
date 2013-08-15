"""
links:
http://www.smart.net/~mmontes/ushols.html

calendar query language
project name "CalQLUS", "CQL"

All PATTERNs can be reduced/converted to MASKs

PATTERNs are the "patterns", a compact structure that
describes regular, repeated CODE entries.

MASKs are the explicit non-compact structures that
describe the days on a calendar over a given range

Definitions:

DATE
(YYYY,DDD) tuple
Julian day (day in the year, 1-366)
-----------------------------------------
MASK_ELEMENT
is a (DATE_RANGE:CODE_SEQUENCE) tuple
-----------------------------------------

WEEK
collection of 7 DAYs Mon-Sun

DAY
integer in range 0-6 corresponding to Mon-Sun
each DAY is associated with a SEQUENCE

SEQUENCE
sequence of CODEs that are repeated 
 
CODE
1-24 = working (hours)
S = sick leave
V = vacation
L = leave w/o pay
W = leave w/ pay
-----------------------------------------

Operation:
"""

from UserList import UserList
import time
time.daylight = 0

OK_CODES = ['S','V','L','W'] + range(1,25)
NIL = '*'
NILS = [None,NIL,'']


class Day(UserList):
    "date stored to day precision"
    def __init__(self,tup):
        if type(tup) in [type(1),type(1.0)]:
            tup = Day.secs_to_yyyydd(tup)
        yyyy,dd = tup
        UserList.__init__(self, [yyyy,dd])

    def __add__(self,n):
        "return date that is n days later than self"
        secs = Day.epoch_secs(self) + n * 3600 * 24
        return Day(secs)

    def __sub__(self,day):
        "return number of days between self and day inclusive"
        diff = int (Day.secs_to_days(Day.epoch_secs(self) - Day.epoch_secs(day)) )
        return diff

    def __hash__(self):
        return hash(tuple(self))

    def __repr__(self):
        return time.strftime("%Y/%m/%d", time.strptime("%s%03d" % tuple(self),"%Y%j") )

    def fmt(self,f):
        "return string representation of self of given strptime format f"
        return time.strftime(f,time.strptime("%s%03d" % tuple(self),"%Y%j"))
    
    import time
    def epoch_secs(tup):
        "return yyyy,ddd tuple as secs"
        yyyy,ddd = tup
        tup = list(time.strptime("%s%03d" %(yyyy,ddd),"%Y%j"))
        tup[8] = 0
        tup=tuple(tup)
        return int(time.strftime('%s',tup))

    epoch_secs = staticmethod(epoch_secs)

    def secs_to_yyyydd(secs):
        tup = time.gmtime(secs)
        return (tup[0],tup[7])

    secs_to_yyyydd = staticmethod(secs_to_yyyydd)

    def mon_sun(tup):
        "return yyyy,ddd tuple as mon-sunday decimal [1-7]"
        yyyy,ddd = tup
        tup = time.strptime("%s%03d" % (yyyy,ddd),"%Y%j")
        num = time.strftime("%u",tup)
        return int( num)

    mon_sun = staticmethod(mon_sun)
    
    def secs_to_days(s):
        "convert secs to days"
        return s / (60 *60 * 24)

    secs_to_days = staticmethod(secs_to_days)

    def intersect(dr_x,dr_y):
        "get intersection of date ranges x and y"
        (x_st,x_end) = dr_x
        (y_st,y_end) = dr_y

        r_st = y_st
        if Day.epoch_secs(x_st) > Day.epoch_secs(y_st):
            r_st = x_st
        r_end = y_end    
        if Day.epoch_secs(x_end) < Day.epoch_secs(y_end):
            r_end = x_end

        if Day.epoch_secs(r_st) > Day.epoch_secs(r_end):
            return None

        return (r_st,r_end)    
        
    intersect = staticmethod(intersect)

class FlatCalendar(UserList):
    "output ready simple data structure"
    def __init__(self,dd,arr):
        self.st_dt = dd
        self.pats = [[] for i in range(len(arr))]
        UserList.__init__(self,arr)

    def __repr__(self):
        "return calendar as formatted string"
        s = ''
        m_seq = self
        num_days = len(m_seq)
        s += "num_days = %d\n" % num_days
        e_sec = Day.epoch_secs(self.st_dt)
        for i in range(num_days):
            s+= '%s:%s\n' % (time.strftime("%a %D",
                                           time.gmtime(e_sec + i * 3600 * 24)),
                             m_seq[i])
        return s    

    def set(self,dt,val,inst=1):
        "given date, set at that index to val"
        idx = Day(dt) - self.st_dt
        self[idx] = val
        self.pats[idx].append(inst)
        return val

    def get(self,dt):
        idx = Day(dt) - self.st_dt
        return self[idx]

    def date_range(self):
        num_days = len(self)
        st_dt = self.st_dt
        end_dt = st_dt + (num_days - 1)
        return (Day(st_dt),Day(end_dt))


class AbstractPattern:
    "abstract pattern class"
    pass

class WeeklyPattern(AbstractPattern):
    """weekly pattern
a two-tuple 
'date_range':(start_date_inclusive,end_date_inclusive),
start_date must be > 1995
for which a given WEEK applies
"""
    def __init__(self,dr,week):
        self.dr = dr
        self.week = week

    def __repr__(self):
        s = "date_range:%s\n" % (self.dr,)
        for wd,d in zip(['Mo','Tu','We','Th','Fr','Sa','Su'],self.week):
            s += "%s:%s\n" % (wd,d)
        return s   
        
    def date_range(self):
        "return date_range"
        return self.dr

    def apply_to(self,fcal):
        """apply pattern over flat calendar (on overlapping date ranges)"""
        dr = Day.intersect(self.date_range(),fcal.date_range())
        p_week = self.week
        p_x = 0
        num_days = 0
        if dr is not None:
            num_days = (dr[1] - dr[0]) + 1
            p_x = dr[0] - fcal.date_range()[0]

        c_flag = 0

        st_day = fcal.date_range()[0]
        ## get nominal start day [Mon-Sun] or [0-6]
        ms_day = Day.mon_sun(fcal.date_range()[0]) - 1
        
        marks = [0,0,0,0,0,0,0]

        ## cycle marks from monday to start day
        for i in range(0,(ms_day+p_x) % 7):
            self.cycle(marks,p_week,i)

        for i in range(p_x,p_x+num_days):
            day = (ms_day + i) % 7
            if len(p_week[day]) > 0:

                if p_week[day][marks[day] % len(p_week[day])]  not in NILS:
                    c_flag += 1
                    val = self.cycle(marks,p_week,day)
                    fcal.set(st_day + i,val,self)
                else:
                    val = self.cycle(marks,p_week,day)
                    
        assert c_flag, "flat_calendar has not changed by pattern: %s" % (p_week,)
        return fcal

    def cycle(marks,lol,idx):
        "cycle through lists in list of lists, saving index markers in marks"
        el_idx = marks[idx]
        res = lol[idx][el_idx % len(lol[idx])]
        marks[idx] += 1
        return res

    cycle = staticmethod(cycle)

class DailyPattern(AbstractPattern):
    """SEQUENCE, plus the DATE_RANGE associated with it"""
    def __init__(self,hash):
        assert len(hash.keys()) > 0, "hash needs to have at least one element!" 
        self.hash = hash

    def __repr__(self):
        s = ''
        ks = self.hash.keys()
        ks.sort()
        for k in ks:
            s += '%s:%s\n' %(k,self.hash[k])
        return s
    
    def date_range(self):
        "return daterange"
        ks = self.hash.keys()
        ks.sort()
        if len(ks) > 0:
            end_dt = ks[-1]
            st_dt = ks[0]
            return (Day(st_dt),Day(end_dt))
        else:
            return None

    def apply_to(self,fcal):
        """apply pattern over flat calendar (on overlapping date ranges)"""
        ks = self.hash.keys()
        ks.sort()
        c_flag = 0
        dr = Day.intersect(self.date_range(),fcal.date_range())
       
        if dr is None:
            num_days = 0
        else:
            num_days = (dr[1] - dr[0]) + 1
            

        for i in range(num_days):
            day = dr[0] + i
            if day in ks:
                val = self.hash[day]
                elt = fcal.get(day)
                if val in NILS:
                    continue
                if val != elt:
                    fcal.set(day,val,self)
                    c_flag = 1
                    
        assert c_flag, "flat_calendar has not changed by pattern: %s" % (self.hash,)
        return fcal
        

sample_mask = (
    ((1999,100),(1999,101)),
    ['8','V']
    )

sample_pattern = (
    ((1997,100),(1998,305)),
    [NIL,
     NIL,
     NIL,
     NIL,
     NIL,
     NIL,
     (2,8,'V')]
    )



from random import choice

def gen_fcal(dr):
    "randomly generate flat calendar given dateragne" 
    st_dt,end_dt = dr
    num_days = end_dt - st_dt + 1
    return FlatCalendar(st_dt,[choice(OK_CODES + [NIL]) for i in range(num_days)])

def gen_daily(dr):
    "randomly generate daily given daterange"
    st_dt,end_dt = dr
    num_days = end_dt - st_dt + 1
    hash = {}
    for i in range(num_days):
        hash[tuple(st_dt + i)] = choice(OK_CODES + [NIL])
    return DailyPattern(hash)    

def gen_weekly(dr):
    "randomly generate weekly given daterange"
    res = []
    for i in range(7):
        wday = []
        for j in range(choice(range(5))):
            wday.append(choice(OK_CODES + [NIL]))
        res.append(wday)
    return  WeeklyPattern(dr,res)   
    
    
if __name__=='__main__':
    import sys
    dr1 = Day((1999,10)),Day((2001,225))
    dr2 = Day((1998,10)),Day((2000,125))

    dr3 = Day((1999,10)),Day((1999,35))
    fcal = gen_fcal(dr3)
    print fcal

    dpat = gen_daily(dr3)
    print dpat

    fcal = dpat.apply_to(fcal)
    print fcal

    wpat = gen_weekly(dr3)
    print wpat


    fcal = wpat.apply_to(fcal)
    print fcal
