###############################################################################
# pickling
#

from util import *


def binsave(filename, var):
    cPickle.dump(var, openStream(filename, "w"), 2)

def binload(filename):
    return cPickle.load(openStream(filename))

def varset():
    if "varset" not in GLOBALS():
        GLOBALS()["varset"] = {}
    return GLOBALS()["varset"]

def addvar(* varnames):
    for name in varnames:
        varset()[name] = 1

def delvar(* varnames):
    for name in varnames:
        del varset()[name]

def getvars(table):
    set = subdict(table, varset())
    return set

def setvars(table, dct):
    for name in dct:
        table[name] = dct[name]

def showvars(table=None, width=70, out=sys.stdout):
    names = varset().keys()
    names.sort()
    
    if not table:
        printcols(names, width, out)
    else:
        maxname = max(map(len, names))
        
        
        for name in names:
            out.write(name + " "*(maxname-len(name)) + "  ")
            out.write("type: " + type(table[name]).__name__)
            
            if "__len__" in dir(table[name]):
                out.write(", size: %d\n" % len(table[name]))
            else:
                out.write("\n")
            


def saveall(table, filename = "all.pickle"):
    binsave(filename, getvars(table))
    
    # display variables saved
    keys = varset().keys()
    keys.sort()
    for key in keys:
        log("%s: saved '%s'" % (filename, key))

def loadall(table, filename = "all.pickle"):
    set = binload(filename)
    setvars(table, set)
    
    # also add new var names to varset
    set2 = varset()
    keys = set.keys()
    keys.sort()
    for key in keys:
        set2[key] = 1
        log("%s: loaded '%s'" % (filename, key))
        
def clearall():
    varset().clear()
