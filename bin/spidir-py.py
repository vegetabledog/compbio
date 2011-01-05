#!/usr/bin/env python
#
# SPIDIR - SPecies Informed DIstance-based Reconstruction
# Matt Rasmussen
# May 2006
#

# python libs
import copy
import math
import os
import random
import StringIO
import sys

# rasmus libs
from rasmus import progress
from rasmus import stats
from rasmus import treelib
from rasmus import util

# rasmus.bio libs
from rasmus.bio import genomeutil
from rasmus.bio import fasta
from rasmus.bio import phylip
from rasmus.bio import phylo

# spidir lib
import Spidir



# command line options
options = ["""\
  SPIDIR v0.7 (beta) Sept 2007
  SPecies Informed DIstanced-base Reconstruction
  Matt Rasmussen
    
""",
 "Options",
 ["o:", "out=", "out", "<output prefix>",
    {"help": "The prefix for all output files", 
     "single": True,
     "default": "spidir"}],
 
 ["d:", "dist=", "dist", "<distance file>", 
    {"help": "Build a tree from a phylip distance matrix file"}],

 ["l:", "labels=", "labels", "<gene labels file>", 
    {"help": "Supply gene names for the rows and cols of a distance matrix"}],
     
 ["p:", "param=", "param", "<param file>",
    {"help": "When training this is used as an output file",
     "single": True}],
 ["s:", "stree=", "stree", "<species tree>",
    {"single": True,
     "help": "species tree (newick format)"}],
 ["S:", "smap=", "smap", "<gene2species map>",
    {"help": "mapping of gene names to species names"}],
     
 
 "Search options",
 ["R:", "search=", "search", "<method>",
    {"default": ["mcmc"],
     "help": """\
    tree search method.  Options are:
        mcmc   - Markov Chain Monte Carlo (default)
        greedy - Phylip-like search
        none   - no search"""}],
 ["T:", "tree=", "tree", "<propose tree>",
    {"default": []}],
 ["", "tops=", "tops", "<proposed topologies>",
    {"default": []}],
 ["i:", "iters=", "iters", "<MCMC iterations>", 
    {"default": 500, 
     "parser": int,
     "single": True}],
 ["I:", "depth=", "depth", "<greedy NNI depth>",
    {"default": 3,
     "parser": int,
     "single": True}],
 
 ["", "rerootprob=", "rerootprob", "<probability of reroot>",
    {"single": True,
     "default": 1,
     "parser": float}],
 ["", "nchains=", "nchains", "<number of chains>",
    {"single": True,
     "default": 2,
     "parser": int}],
 ["", "eprune=", "eprune", "<exhaustive prune>",
    {"single": True,
     "default": -10,
     "parser": float}],
 ["", "searchtest", "searchtest", "",
    {"single": True}],
 ["", "regrafts=", "regrafts", "<regraph iterations>",
    {"single": True,
     "parser": int,
     "default": 100}],
 ["", "regraftloop=", "regraftloop", "<number of branches to try for each regraft>",
    {"single": True,
     "parser": int,
     "default": 40}],

 "Training options",
 ["t", "train", "train", "",
    {"help": """\
    Run SPIDIR in training mode.  """,
    "single":True}],
 ["z:", "trainstats=", "trainstats", "<training stats prefix>",
    {"single": True,
     "default": ""}],
 #["e:", "trainext=", "trainext", "<training tree extension>",
 #   {"single":True}],
 
 "Parameter options",
 ["D:", "dupprob=", "dupprob", "<probability of duplication>",
    {"default": 1,
     "parser": float,
     "single": True}],
 ["", "predupprob=", "predupprob", "<probability of pre-speciation duplication>",
    {"default": .01,
     "parser": float,
     "single": True}],
 ["L:", "lossprob=", "lossprob", "<probability of loss>",
    {"default": 1,
     "parser": float,
     "single": True}],
 ["", "errorcost=", "errorcost", "<error cost>",
    {"single": True,
     "default": -200,
     "parser": float}],
 ["", "famprob=", "famprob", "True|False",
    {"default": True,
     "parser": util.str2bool,
     "single": True}],
 
 "Miscellaneous options",
 ["", "correcttree=", "correcttree", "<correct tree newick>",
    {"single": True,
     "parser": treelib.read_tree}],
 ["V:", "debug=", "debug", "<level>",
    {"single": True,
     "default": 0, 
     "parser": int,
     "help": "set SPIDIR debug level"}],
 ["", "python_only", "python_only", ""],
 ["", "parsimony", "parsimony", ""],
 ["", "mlhkydist", "mlhkydist", ""],
 ["g", "generate_int", "generate_int", "",
    {"single": True}],
 ["", "bgfreq=", "bgfreq", "<background base frequencies>",
    {"parser": lambda x: map(float,x.split(',')),
     "default": [.25, .25, .25, .25],
     "single": True}],
 ["", "tsvratio=", "tsvratio", "<transition/transversion ratio>",
    {"parser": float,
     "default": .5,
     "single": True}],

 ["P:", "paths=", "paths", "<files path>",
    {"single": True,
     "help": "colon separated paths used to search for data files",
     "default": "."}],
 ["h", "help", "help", "", 
    {"single": True,
     "help": "display program usage"}],
     
"""
Examples:

1. training evolutionary model (execute in spidir-examples/ directory)

    spidir.py -t -p model.param -s yeast.stree -S yeast.smap yeast-one2one/*.nt.tree
    
    Trains a model (saved in the file 'model.param') from the genes trees 
    'yeast-one2one/*.nt.tree' using a species tree 'yeast.stree' and a gene-to- 
    species mapping 'yeast.smap'.
    
2. gene tree reconstruction

    spidir.py -p yeast.param -s yeast.stree -S yeast.smap \\
        -d yeast-one2one/0.nt.align.dist \\
        -l yeast-one2one/0.nt.align \\
        -o mytree
        
    Reconstructs the gene tree (will be saved in 'mytree.tree') for the pair-wise
    distance matrix  'yeast-one2one/0.nt.align.dist' with gene names in
    'yeast-one2one/0.nt.align' using a model of evolution 'model.param' (must be
    created by training first), a specie stree 'yeast.stree', and a gene-to-
    species mapping 'yeast.smap'.
    
"""
]

# import Spidir's debug function
debug = Spidir.debug


def main(argv):   
    # parse options
    conf = util.parseOptions(argv, options, quit=True, helpOption=False)

    if conf["help"]:
        util.usage(os.path.basename(argv[0]), options)
        sys.exit(1)
    
    # setup debug output
    #Spidir.setDebugStream(file(Spidir.debugFile(conf), "w"))
    
    if conf["debug"] > 0:
        util.globalTimer().removeStream(sys.stderr)
        util.globalTimer().addStream(sys.stdout)
        debug("SPIDIR")
        debug("configuration:")
        util.printDict(conf, justify=lambda x: "left", out=Spidir.DEBUG)
        debug()
        debug()
    
    
    genomeutil.readOptions(conf)
    conf["specprob"] = 1.0 - conf["dupprob"]
    
    # read input
    gene2species = conf["gene2species"]
    stree = conf["stree"]
    
    if conf["train"]:
        trainTree(conf, stree, gene2species)
    else:
        buildTree(conf, stree, gene2species)




def trainTree(conf, stree, gene2species):
    args = conf["REST"]
    treefiles = []
    
    for arg in args:
        treefiles.extend(util.shellparser(arg))

    util.tic("reading trees")
    trees = []
    prog = progress.ProgressBar(len(treefiles))
    for treefile in treefiles:
        prog.update()
        trees.append(treelib.read_tree(treefile))
        
        # even out top two branches
        totlen = trees[-1].root.children[0].dist + \
                 trees[-1].root.children[1].dist
        trees[-1].root.children[0].dist = totlen / 2.0
        trees[-1].root.children[1].dist = totlen / 2.0
        
    util.toc()
    
    params = Spidir.learnModel(trees, stree, gene2species, conf["trainstats"],
                               filenames=treefiles)
    
    Spidir.writeParams(conf["param"], params)
    
    


def buildTree(conf, stree, gene2species):
    params = Spidir.readParams(conf["param"])
    
    if "correcttree" in conf:
        conf["correcthash"] = phylo.hash_tree(conf["correcttree"])
    
    
    if "dist" in conf:
        for i in range(len(conf["dist"])):
            distfile = conf["dist"][i]
            
            labels, distmat = phylip.read_dist_matrix(distfile)
        
            # read in different labels if needed
            if "labels" in conf:
                labels = Spidir.readLabels(conf["labels"][i])
                conf["aln"] = fasta.readFasta(conf["labels"][i])
            
            tree, logl = Spidir.spidir(conf, distmat, labels, stree, 
                                          gene2species, params)
            tree.write(Spidir.outTreeFile(conf))
            
            # test for correctness
            if "correcttree" in conf:
                correctTree = conf["correcttree"]
                phylo.hash_order_tree(correctTree)
                phylo.hash_order_tree(tree)
                
                thash1 = phylo.hash_tree(tree)
                thash2 = phylo.hash_tree(correctTree)
                
                print "spidir: "
                treelib.draw_tree(tree, maxlen=5, minlen=5)
                print
                
                print "correct:"
                treelib.draw_tree(correctTree, maxlen=5, minlen=5)
                print
                
                if len(tree.leaves()) > 3:
                    rferror = Spidir.robinson_foulds_error(correctTree, tree)
                else:
                    rferror = 0.0
                
                if thash1 == thash2:
                    print "CORRECT TREE FOUND"
                else:
                    print "WRONG TREE FOUND (RF: %f)" % rferror
            


#
# run as script
#
if __name__ == "__main__":
    try:
        main(sys.argv)
    except util.OptionError, e:
        print >>sys.stdout, "%s: %s" % (os.path.basename(sys.argv[0]), e)
        sys.exit(1)


