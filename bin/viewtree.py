#!/usr/bin/env python

import sys, optparse
from rasmus import util, env, treelib
from rasmus.bio import phylo, genomeutil, paml
from rasmus.vis import treesvg
from rasmus import tablelib

o = optparse.OptionParser()
o.set_defaults(tree=[],
               scale=20,
               minlen=1,
               maxlen=10000)

o.add_option("-t", "--tree", dest="tree",
             metavar="<newick file>",
             action="append")
o.add_option("-l", "--scale", dest="scale",
             metavar="<scaling>",
             type="float")
o.add_option("-m", "--minlen", dest="minlen",
             metavar="<minimum branch length>",
             type="int")
o.add_option("-M", "--maxlen", dest="maxlen",
             metavar="<maximum branch length>",
             type="int")
o.add_option("-i", "--hist", dest="hist",
             action="store_true",
             default=False,
             help="output histogram of tree topologies")
o.add_option("--histsplit", dest="histsplit",
             action="store_true",
             default=False,
             help="output histogram of tree splits")
o.add_option("--hashes", dest="hashes",
             action="store_true",
             default=False)
o.add_option("-n", "--names", dest="names",
             action="store_true",
             default=False,
             help="display internal node names")
o.add_option("--snames", dest="snames",
             action="store_true",
             default=False,
             help="display species names")
o.add_option("-N", "--newick", dest="newick",
             action="store_true",
             default=False,
             help="write newick format")
o.add_option("--len", dest="len",
             action="store_true",
             default=False,
             help="display branch lengths")
o.add_option("-r", "--reroot", dest="reroot",
             metavar="<branch to root tree>")
o.add_option("-c", "--colormap", dest="colormap",
             metavar="<color map file>")
o.add_option("--rootby", dest="rootby",
             metavar="dup|loss|duploss")
o.add_option("-d", "--dump", dest="dump",
             action="store_true",
             default=False,
             help="covert to easy to parse format")
o.add_option("-H", "--headings", dest="headings",
             action="store_true",
             default=False,
             help="show heading information above each tree")
o.add_option("-g", "--graphical", dest="graphical",
             metavar="<filename>|-")
o.add_option("-G", "--default-graphical", dest="default_graphical",
             action="store_true",
             default=False)
o.add_option("-e", "--events", dest="events", 
             action="store_true",
             default=False)
o.add_option("--paml-labels", dest="paml_labels",
             action="store_true",
             default=False)
o.add_option("-s", "--stree", dest="stree",
             metavar="<species tree>",
             help="species tree (newick format)")
o.add_option("-S", "--smap", dest="smap",
             metavar="<gene2species map>",
             help="mapping of gene names to species names")
#o.add_option(
#  ["", "trees=", "trees", "{trees}",
#   {"single": True,
#    "parser": util.shellparser,
#    "default": []}]
#] + genomeutil.options

options, args = o.parse_args()
options.tree.extend(args)

conf = dict((k,v) for k,v in options.__dict__.items() if v is not None)
conf["trees"] = []
conf["REST"] = []


# parse options
#conf = util.parseOptions(sys.argv, options, quit=True, resthelp="<trees> ...")
#genomeutil.readOptions(conf)

if options.smap:
    gene2species = genomeutil.readGene2species(options.smap)
else:
    gene2species = lambda x: x
if options.stree:
    stree = treelib.readTree(options.stree)
else:
    stree = None

if options.colormap:
    colormap = treelib.readTreeColorMap(options.colormap)
else:
    colormap = None


hashes = []
splits = []
ntrees = 0

if options.reroot:
    if options.reroot.isdigit():
        options.reroot = int(options.reroot)


def iterTrees(treefile):
    ntrees = 0
    infile = util.openStream(treefile)
    
    while True:
        try:
            if options.paml_labels:
                tree = paml.readTree(infile)
            else:
                tree = treelib.readTree(infile)
            ntrees += 1
            yield tree
        except Exception, e:
            if ntrees < 1:
                print >>sys.stderr, e
            break
            

def processTree(tree):
    global gene2species, ntrees, stree
    ntrees += 1

    if stree is not None and gene2species is not None and \
       options.rootby is not None:
        phylo.reconRoot(tree, stree, gene2species, 
                            rootby=options.rootby,
                            newCopy=False)
    
    elif options.reroot is not None:
        tree = treelib.reroot(tree, options.reroot)
        
    
    if options.hist or options.hashes:
        # only count the tree in histogram mode
    
        thash = phylo.hashTree(tree, gene2species)
        hashes.append(thash)
    
    
    elif options.histsplit:
        for leaf in tree.leaves():
            tree.rename(leaf.name, gene2species(leaf.name))
        splits.extend(phylo.findSplits(tree))
    
    
    elif options.dump:
        # dump mode
        
        names = util.sort(tree.nodes.keys())
        
        print "# node  path-to-root"
        for name in names:
            path = []
            ptr = tree.nodes[name]
            while ptr != tree.root:
                ptr = ptr.parent
                path.append(ptr.name)
            
            print "%s\t%s" % (name, ",".join(map(str, path)))
        print 
        
        print "# node branch-length"
        for name in names:
            print "%s\t%f" % (name, tree.nodes[name].dist)
    
    else:
        # default mode: display tree
        
        if options.headings:
            print
            print "------------------------------------------------"
            print "filename: %s" % treefile
            print "treelen:  %f" % sum(x.dist for x in tree.nodes.values())
            print
        
        
        # set default graphical settings
        if options.default_graphical:
            if options.graphical is None:
                options.graphical = "-"
            options.scale = 500.0


        labels = {}
        
        for node in tree.nodes.values():
            labels[node.name] = ""
        
        if options.events:
            assert stree != None and gene2species != None
            phylo.initDupLossTree(stree)
            phylo.countDupLossTree(tree, stree, gene2species)
            phylo.countAncestralGenes(stree)
            
            for node in stree:
                labels[node.name] = "%d" % node.data['genes']
                
                if node.data['dup'] > 0:
                    labels[node.name] += " +%d" % node.data['dup']
                    
                if node.data['loss'] > 0:
                    labels[node.name] += " -%d" %  node.data['loss']
            tree = stree
            stree = None
            gene2species = None

        if options.snames:
            assert stree is not None and gene2species is not None
            recon = phylo.reconcile(tree, stree, gene2species)
        
        # create branch labels
        for node in tree.nodes.values():

            # label distances
            if options.len:
                labels[node.name] += "%f" % node.dist
            
            # label bootstraps
            if "boot" in node.data and node.data["boot"] != 0:
                if isinstance(node.data["boot"], int):
                    labels[node.name] = "(%d) %s" % (node.data["boot"], 
                                                     labels[node.name])
                else:
                    labels[node.name] = "(%.2f) %s" % (node.data["boot"], 
                                                       labels[node.name])

            # label node names
            if options.names and not node.isLeaf():
                labels[node.name] = "[%s] %s" % (node.name, 
                                                 labels[node.name])

            if options.snames:
                labels[node.name] = "%s %s" % (str(recon[node].name),
                                               labels[node.name])

            # paml branch lables
            if options.paml_labels and "label" in node.data:
                labels[node.name] = "#%d %s" % (node.data["label"],
                                                labels[node.name])
        
        if options.graphical is not None:
            if options.graphical == "-":
                treesvg.showTree(tree, labels=labels,
                                       xscale=options.scale,
                                       minlen=options.minlen,
                                       maxlen=options.maxlen,
                                       legendScale=True,
                                       colormap=colormap,
                                       stree=stree,
                                       gene2species=gene2species)
            else:
                treesvg.drawTree(tree, labels=labels,
                                       xscale=options.scale,
                                       minlen=options.minlen,
                                       maxlen=options.maxlen,
                                       filename=options.graphical,
                                       legendScale=True,
                                       colormap=colormap,
                                       stree=stree,
                                       gene2species=gene2species)
        elif options.newick:
            tree.write()
        else:
            treelib.drawTree(tree, labels=labels,
                             scale=options.scale,
                             minlen=options.minlen,
                             maxlen=options.maxlen)




for treefile in options.tree:
    for tree in iterTrees(treefile):
        processTree(tree)
    
# display topology histogram
if options.hist:
    histogram = tablelib.histTable(hashes)
    histogram.write(sys.stdout)

# display splits histogram
if options.histsplit:
    s2 = []
    for set1, set2 in splits:
        s2.append(" ".join(set1) + "  |  " + " ".join(set2))
    histogram = tablelib.histTable(s2)
    
    # modify percentages to total number of trees
    splits_per_tree = len(splits) / ntrees
    for row in histogram:
        row["percent"] *= splits_per_tree
    
    histogram.write(sys.stdout)

if options.hashes:
    for thash in hashes:
        print thash

'''
options = [
#  ["t:", "tree=", "tree", "<newick file>",
#    {"default": []}],
  ["l:", "scale=", "scale", "<scaling>",
    {"default": 20,
     "single": True,
     "parser": float}],
  ["m:", "minlen=", "minlen", "<minimum branch length>",
    {"default": 1,
     "single": True,
     "parser": int}],  
  ["M:", "maxlen=", "maxlen", "<maximum branch length>",
    {"default": 10000,
     "single": True,
     "parser": int}],
  ["i", "hist", "hist", "",  
    {"single": True,
     "help": "output histogram of tree topologies"}],
  ["", "histsplit", "histsplit", "",  
    {"single": True,
     "help": "output histogram of tree splits"}],
  ["", "hashes", "hashes", "",
    {"single": True}], 
  ["n", "names", "names", "",
    {"single": True,
     "help": "display internal node names"}],
  ["", "snames", "snames", "",
    {"single": True,
     "help": "display species names"}],
  ["N", "newick", "newick", "",
    {"single": True,
     "help": "write newick format"}],
  ["", "len", "len", "",
    {"single": True,
     "help": "display branch lengths"}],
  ["r:", "reroot=", "reroot", "<branch to root tree>",
    {"single": True}],
  ["c:", "colormap=", "colormap", "<color map file>",
    {"single": True}],
  ["", "rootby=", "rootby", "dup|loss|duploss",
    {"single": True,
     "default": "duploss"}],
  ["d", "dump", "dump", "",
    {"single": True,
     "help": "covert to easy to parse format"}],
  ["H", "headings", "headings", "",
    {"single": True,
     "help": "show heading information above each tree"}],
  ["g:", "graphical=", "graphical", "<filename>|-",
    {"single": True}],
  ["G", "default-graphical", "default-graphical", "",
    {"single": True}],
  ["e", "events", "events", "",
    {"single": True}],
  ["", "paml-labels", "paml-labels", "",
   {"single": True}],
  ["", "trees=", "trees", "{trees}",
   {"single": True,
    "parser": util.shellparser,
    "default": []}]
] + genomeutil.options

'''
