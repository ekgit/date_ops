#!/usr/bin/python2
"""do date operations on specified fields in file
date_ops -f filename -v format1 -v format2 ... -v formatN [-d default1 -d default2 ... -d defaultN] -e eval_string 

-f filename
-v formats
    example:
        if byte range 1-8 contains 20011231, specify byte-range and format as
        "n1-n2:%Y%m%d"

-d defaults
    if format cannot be processed on given string, default string value is used instead
-e eval string

each format is assigned to variable vN,
e.g. format0 parses variable v0,
     format1 parses variable v1,
     etc...


example: find last day of month for given date
echo 20011201|python ~ekim/src/date_ops/date_ops.py -f - -v "1-8:%Y%m%d" -e "last_day(v0.year,v0.month)"

"""

import time,datetime


def gen_pp_table():
    r = {}
    s = datetime.date(1950,1,8)
    while s < datetime.date(2050,1,10):
        yr = s.year
        r[yr] = []
        while s.year == yr:
            r[yr].append( ((s,s + datetime.timedelta(6)),
                           (s + datetime.timedelta(7),s + datetime.timedelta(13))))
            s += datetime.timedelta(14)
    return r

PP_TABLE = gen_pp_table()
def pp_calc(yy,pp):
    'return date ranges for payperiods based on yr 2000 start = jan2 with 27 pay periods '

    ## normalize year
    if yy < 50:
        yy += 2000
    return PP_TABLE[yy][pp-1]
            

    
def split_fmt(fmt):
    idx = fmt.find(':')
    br = map(int,fmt[:idx].split('-'))
    fmt = fmt[idx+1:]
    return (br,fmt)

def tuplize(s,fmt):
    "return yyyymmdd string as time tuple"
    ## split fmt into byte-ranges and fmt
    br,fmt = split_fmt(fmt)
    return time.strptime(s[br[0]-1:br[1]],fmt)

def tup2dt(tup):
    "convert tuple to datetime obj"
    return datetime.date(tup[0],tup[1],tup[2])

def s2dt(s,fmt):
    t = time.strptime(s,fmt)
    return apply(datetime.date,t[:3])

def last_day(y,m=None):
    rv = None
    if m is None:
        rv = datetime.datetime(y,1,1) + datetime.timedelta(370)
        rv = datetime.datetime(rv.year,1,1)
        rv -= datetime.timedelta(1)
    else:
        rv = datetime.datetime(y,m,1) + datetime.timedelta(35)
        rv = datetime.datetime(rv.year,rv.month,1)
        rv -= datetime.timedelta(1)
    return rv

def t(code,n):
    try:
        return eval(code)
    except:
        return " " * n
            
if __name__ == '__main__':
    import sys,getopt
    fmt = "%Y%m%d"

    p = {'e':'"foo"'}
    fmts = []
    defaults = []
    try:
        opts,args=getopt.getopt(sys.argv[1:],"f:v:e:d:")
    except:
        print "usage"
        print __doc__
        sys.exit()
        
    for o,a in opts:
        if o in ('-f','-e'):
            p[o[-1]] = a
        if o in ('-v'):
            fmts.append(a)
        if o in ('-d'):
            defaults.append(a)

        
    fp = sys.stdin
    if p.has_key('f'):
        fp = open(p['f'])
    for ln in fp:
        d = {}
    ## populate vars
        #print ln,
        for fmt,n in zip(fmts,range(len(fmts))):
            d['ln'] = ln
            try:
                d['v%s' % n] = tup2dt(tuplize(ln,fmt))
            except:
                try:
                    br,junk = split_fmt(fmt)
                    nln = ln[:br[0]-1] + defaults[n] + ln[br[1]:]
                    d['v%s' % n] = tup2dt(tuplize(nln,fmt))
                except:    
                    sys.stderr.write(ln +  "can't convert to time\n")

            #print d
        try:
            d.update(locals())
            print eval(p['e'],d)
        except:
            print "can't eval",  sys.exc_type, sys.exc_value
            print "*" + ln
                
            
            
            
#        secs = time.mktime
#        years = secs/(3600.00 * 24 * 365.25)
#        print "%6.2f" % float(years * 12)
    
