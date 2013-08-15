from warnings import warn
import sys

################################################################################
# date funcs/classes
################################################################################

import datetime
class Present(datetime.date):
    def __init__(self, year=9999, month=12, day=31,  hour=0, minute=0, second=0, microsecond=0,  tzinfo=None):
        datetime.date.__init__(self, year, month, day,hour, minute, second, microsecond,  tzinfo)
    def __repr__(self):
        return "P:%s" % datetime.date.__repr__(self)
    def __str__(self):
        return "P:%s" % datetime.date.__str__(self)

class Unknown(datetime.date):
    def __repr__(self):
        return "Unknown:%s" % datetime.date.__repr__(self)
    def __str__(self):
        return "Unknown:%s" % datetime.date.__str__(self)
    
class DateRange:
    def __init__(self,left,right):
        #assert left <= right, "%s <= %s" % (left,right)
        self.left = left
        self.right = right
    def ____or__(self,other):
        "|  = union"
        left = min( self.left , other.left)
        right = max(self.right,other.right)
        return DateRange(left,right)

    def __and__(self,other):
        "& = intersection"
        left = max(self.left,other.left)
        right = min(self.right,other.right)
        max_right = max(self.right,other.right)
        ## if non-present date is > present, that date supersedes
        #if type(max_right) != Present and type(right) == Present:
        #    right = Present(max_right.year,max_right.month,max_right.day)
        if left > right:
            return None
        return DateRange(left,right)

    def __sub__(self,other):
        "return list of date ranges in this date range but not the other"
        rv = []
        i = self & other

        ## if no intersection, return self
        if  i == None:
            return [self]
        ##if intersection encompasses self, return None
        if (i.left <= self.left and i.right >= self.right):
            return []

        if i.left > self.left: 
            rv.append(DateRange(self.left,i.left-datetime.timedelta(days=1)))
        if i.right < self.right:
            rv.append(DateRange(i.right+datetime.timedelta(days=1),self.right))
        return rv    

    def __repr__(self):
        return "%s - %s" % (self.left,self.right)

    def days(self):
        return (self.right - self.left).days + 1

import time
def s2dt(s):
    'convert Y-M-D string to date'
    if s.lower() == 'present':
        return Present(9998,12,31)
    tup = time.strptime(s,"%Y-%m-%d")
    return datetime.date(tup[0],tup[1],tup[2])

def s2dt2(s):
    'convert Y-M-D string to date'
    if s.lower() == 'present':
        return Present(9998,12,31)
    tup = time.strptime(s,"%m/%d/%Y")
    return datetime.date(tup[0],tup[1],tup[2])

def endofmonth(yr,mo):
    d = datetime.date(yr,mo,1)
    d += datetime.timedelta(days=35)
    d = datetime.date(d.year,d.month,1)
    d -= datetime.timedelta(days=1)
    return d

################################################################################
# helper functions
################################################################################

def mint(i):
    try:
        return int(i)
    except:
        return 0

def mfloat(f):
    try:
        return float(f)
    except:
        return 0.0

def tfloat(f):
    try:
        return float(f)
    except:
        return None

def filter_if(li,obj=None):
    return filter(lambda x: x is not obj,li)

def row_update(db,key,hash):
    if not db.has_key(key):
        db[key] = {}
    db[key].update(hash)    

def read(fn,fmt):
    fmt = parse_fmt(fmt)
    for ln in open(fn):
        yield parse_ln(fmt,ln)

def set_li(db,k,v):
    "add value to list in k"
    if not db.has_key(k):
        db[k] = []
    db[k].append(v)

def get_pat(db,pat):
    "return val iff pat returns single val"
    li = pat_match(pat,db.keys())
    assert len(li) == 1, "pat: %s should return single val: %s:%s" % (pat,li,db)
    k = li[0]
    return db[k]


################################################################################
# ?
################################################################################

def parse_type(fld):
    'guess what type of field this is'


    while fld.find('.') > -1:
        if fld.rfind('.') == fld.find('.'):
            break
        else:
            fld = fld.replace('.','',1)


    fld = fld.lower()
    
    try:
        fld = fld.replace('-',' ')
        fld = fld.replace('p:',' ')
        
        dt1,dt2 = fld.split()
        dt1 = s2dt2(dt1)
        dt2 = s2dt2(dt2)
        return DateRange(dt1,dt2)
    except:
        for tok in ('$',',',' ','~','p:'):
            fld = fld.replace(tok,'')
        try:
            return float(fld)
        except:
            return str(fld)
    

def calc_ot(rv):
    ot = rv['hrly_rate'] * 1.5 * rv['num_wks'] * rv['avg_ot_hrs']
    return ot

def calc_mn_ot(rv):
    ot = rv['hrly_rate'] * 1.5 * rv['num_wks'] * max(0,rv['avg_ot_hrs'] - 8)
    return ot



def calc_int_payperiod(rv):
    int_date = datetime.date(2004,12,31)
    
    pay_date = rv['dr'].right
    if rv.has_key('pay_date'):
        pay_date = rv['pay_date']
    int_years = (int_date - pay_date).days / 365.0

    
    int_rate = 0
    int_mux = 1.0
    int_type = ''

    if rv['state'] in ['co','co/flsa']:
        int_rate = 0.08
        int_type = 'cpd'
    if rv['state'] in ['or','or/flsa']:
        int_rate = 0.09
        int_type = 'simple'

    if int_type == 'simple':
        int_mux *= (int_rate * int_years)
    elif int_type == 'cpd':
        int_mux *= ((1.0 + int_rate) ** int_years - 1.0)
    else:
        int_mux = 0

    #print "intyears",int_years,int_mux,rv['overtime']
    #return int_mux * (rv['co_hrs_over_12'] + rv['overtime'])
    return int_mux * round_to_cents( rv['overtime'])


def isect_stints(s1,s2):
    'return intersection between s1 and s2, where s2 overrides s1'
    rv = s1.copy()
    dr = rv['dr'] & s2['dr']
    if dr is not None:
        rv.update(s2)
        rv['dr'] = dr
        return rv
    return None

def filter_if(li,obj=None):
    return filter(lambda x: x is not obj,li)

def bimonth_stints(r):
    '''break stints up into bimonthly pay periods'''
    rv = []
    stints = r

    for stint in stints:
        stint_bms = []
        (begin,end) = (stint['dr'].left,stint['dr'].right)
        for yr in range(begin.year,end.year+1):
            for m in range(1,13):
                left = datetime.date(yr,m,1)
                right = datetime.date(yr,m,15)
                pp1 = DateRange(left,right)

                left2 = datetime.date(yr,m,16)
                right2 = endofmonth(yr,m)
                pp2 = DateRange(left2,right2)
                
                pp1_stint = isect_stints({'dr':pp1},stint)
                pp2_stint = isect_stints({'dr':pp2},stint)

                pp_stints = filter_if([pp1_stint,pp2_stint])

                ## reset pay date to 15th or end of month if appropriate
                for pp in (pp1,pp2):
                    for s in pp_stints:
                        if pp.left == s['dr'].left:
                            s['pay_date'] = pp.right
                rv += pp_stints
                stint_bms += pp_stints
        stint['bms'] = stint_bms
    return rv

def round_to_cents(f):
    #return f
    return float("%.2f" % f)


def calc_int(rv):
    'split into bimonthly date ranges and add up interest for each pay period'

    ## add bimonthly stints
    bimonth_stints([rv])
    num_days = rv['dr'].days()

    for x in rv['bms']:
        x['overtime'] = rv['hrly_rate'] * 1.5 * rv['num_wks'] * rv['avg_ot_hrs']
        x['overtime'] *= x['dr'].days() * 1.0 / num_days

        x['overtime'] = round_to_cents(x['overtime'])

    total_int = sum([round_to_cents(calc_int_payperiod(x)) for x in rv['bms']])
    return total_int

def tmp_print(rv):
    print rv['overtime'],[x['overtime'] for x in rv['bms']]
    print '-===== BMS ====='
    for x in rv['bms']:
        print x['dr'],
        if x.has_key('pay_date'):
            print x['pay_date'],

        print x['overtime'],round_to_cents(calc_int_payperiod(x))
    print '--end BMS---'

def has(s,elts):
    for i in elts:
        if s.find(i) > -1:
            return True
    return False

def get_flds(d,fld_names):
    return "\t".join([str(d[n]) for n in fld_names])
    

def addup(*input):
    flds = input[0].keys()
    rv = {}

    for i in input:
        for fld in flds:
            if not i.has_key(fld):
                continue

            if type(i[fld]) in [type(0),type(1.0)]:
                if not rv.has_key(fld):
                    rv[fld] = 0
                rv[fld] += i[fld]
            else:
                if i[fld] != '':
                    rv[fld] = i[fld]
    return rv

if __name__=='__main__':
    import sys,copy

    fld_names = """dr,state,num_wks,avg_ot_hrs,co_hrs_over_12,hrly_rate,overtime,interest,liq_dam,total""".split(',')

    originals = []
    corrections = []



    NAME = None

    for ln in sys.stdin:


        if ln.strip() == '' or ln[0] == ' ':
            continue
        if ln.find('1Dates') == 0:
            continue
        if tfloat(ln[:2]) is None and tfloat(ln[0]) is None:
            NAME = ln.strip()
            continue
        
        ln = ln.strip()
        flds = ln.split('\t')
        
        rv = {}
        corr_rv = {}
        for name,fld in zip(fld_names,
                            [parse_type(fld) for fld in flds]):
            rv[name] = fld
            corr_rv[name] = ''

        ## fix co hrs
        if rv['co_hrs_over_12'] == '':
            rv['co_hrs_over_12'] = 0.0


        ## handle interest recalcs

        #print rv
        if rv['state'] in ['or/flsa','co/flsa']:
            new_interest = calc_int(rv)
            corr_rv['interest'] = new_interest - rv['interest']
            corr_rv['dr'] = rv['dr']

        ## backout FLSA liquidated damages
        if has(rv['state'],['or','co','il']) and 'flsa' in rv['state']:
            corr_rv['liq_dam'] = -1 * rv['liq_dam']
            corr_rv['dr'] = rv['dr']

        ## handle minnesota
        if rv['state'] in ['mn/flsa']:

            corr_rv['overtime'] = calc_mn_ot(rv) - rv['overtime']
            corr_rv['liq_dam'] = calc_mn_ot(rv) - rv['liq_dam']
            corr_rv['avg_ot_hrs'] = max(-8.0,-1 * rv['avg_ot_hrs'])
            corr_rv['dr'] = rv['dr']
            #print 'rv',rv
            #print calc_mn_ot(rv)
            #print 'corr',corr_rv

        ## handle flsa only
        if rv['state'] in ['flsa']:
            corr_rv['overtime'] =  - rv['overtime']
            corr_rv['liq_dam'] =  - rv['liq_dam']
            corr_rv['dr'] = rv['dr']


        ## handle mi (no compensation)
        if has(rv['state'],['mi']):
            corr_rv['overtime'] =  - rv['overtime']
            corr_rv['liq_dam'] = -1 * rv['liq_dam']
            corr_rv['interest'] = -1 * rv['interest']
            corr_rv['dr'] = rv['dr']

        originals.append(rv)
        corrections.append(corr_rv)

    total_sum = 0
    old_total_sum = 0

    to_print = []


    
    for (o,c) in zip(originals,corrections):
        n = addup(o,c)
        old_total_sum += o['total']
        if c['dr'] != '':
            c['dr'] = '*correction'
            n['dr'] = str(o['dr']) + '+'
            n['total'] = sum([n[f] for f in """co_hrs_over_12     overtime        interest        liq_dam""".split()])
            
            o['dr'] = '*' + str(o['dr'])

            to_print.append(o)
            to_print.append(c)
            to_print.append(n)

            total_sum += n['total']
            
        else:
            to_print.append(o)
            total_sum += o['total']


    #print "\t".join(['name: ' + NAME])
    print "\t".join(['Name'] + fld_names)
    for o in to_print:
        print 'name: ' + NAME + "\t" + get_flds(o,fld_names)

    print "\t".join(['name: ' + NAME,"old total: " + "%.2f" % old_total_sum,"new total: " + "%.2f" % total_sum])
    sys.stderr.write("%s\n" % "\t".join([NAME,"%.2f" % old_total_sum,"%.2f" % total_sum]))
    
