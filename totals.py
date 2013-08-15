#!/usr/bin/python2
import time
def tuplize(s):
    "return yyyymmdd string as time tuple"
    return time.strptime(s,"%Y-%m-%d")
  
            
if __name__ == '__main__':
    import sys
    for ln in sys.stdin.readlines():
        (t1,t2) = ln[:10],ln[12:12+10]
        if (t2 == " " * 10):
            t2 = "2003-09-18"
##        print (t1,t2),
        try:
            secs = time.mktime(tuplize(t2)) - time.mktime(tuplize(t1))
            years = secs/(3600.00 * 24 * 365.25)
            
            print years
        except:
            pass
