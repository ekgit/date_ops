import datetime
import time



def tuplize(s,fmt):
    "return yyyymmdd string as time tuple"
    ## split fmt into byte-ranges and fmt

    return time.strptime(s,fmt)

def tup2dt(tup):
    "convert tuple to datetime obj"
    return datetime.date(tup[0],tup[1],tup[2])

            
if __name__=='__main__':
    import sys
    (fr,to) = sys.argv[1:]

    fr = tup2dt(tuplize(fr,'%Y-%m-%d'))
    to = tup2dt(tuplize(to,'%Y-%m-%d'))


    while fr <= to:
        print fr.strftime("%a %Y-%m-%d")
        fr += datetime.timedelta(1)
    

