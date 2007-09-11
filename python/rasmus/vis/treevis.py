"""
    
    Visualization for phylogenetic trees

"""

# rasmus libs
from rasmus import util
from rasmus import treelib
from rasmus.bio import phylo

# summon libs
from summon.core import *
import summon
from summon import sumtree
from summon import shapes


class TreeViewer (sumtree.SumTree):
    def __init__(self, tree, stree=None, gene2species=None, recon=None,
                 dupColor=(1, 0, 0), lossColor=(0, 0, 1), 
                 **options):
        sumtree.SumTree.__init__(self, tree, **options)
        
        self.mode = "gene"
        self.stree = stree                  # species tree
        self.gene2species = gene2species    # gene to species mapping
        self.recon = recon                  # reconciliation
        
        # colors
        self.dupColor = dupColor
        self.lossColor = lossColor
        
        self.setupRecon()
            
    
    def setupRecon(self):
        # construct default reconciliation
        if self.recon == None and self.stree and self.gene2species:
            self.recon = phylo.reconcile(self.tree, self.stree, self.gene2species)
        
        # construct events
        if self.recon:
            self.events = phylo.labelEvents(self.tree, self.recon)
            self.losses = phylo.findLoss(self.tree, self.stree, self.recon)
        else:
            self.events = None
            self.losses = None
    
        
    def show(self):
        sumtree.SumTree.show(self)
        
        # set bindings
        self.win.set_binding(input_key("g"), lambda: self.setMode("gene"))
        self.win.set_binding(input_key("e"), lambda: self.setMode("events"))
        self.win.set_binding(input_key("r"), lambda: self.setMode("reroot"))
        
        if self.events:
            self.win.add_group(self.drawEvents())
    
    
    def drawEvents(self):

        # draw duplications
        dups = [color(*self.dupColor)]        
        for node in self.tree:
            if self.events[node] == "dup":
                dups.append(shapes.box(node.x - .01*self.xscale, node.y - .2,
                                      node.x + .01*self.xscale, node.y + .2))
        
        # draw losses
        losses_per_branch = util.histDict([node for node, schild in self.losses])
        
        losses = [color(*self.lossColor)]
        for node, nlosses in losses_per_branch.iteritems():
            if node.parent == None:
                continue
                
            x1 = node.parent.x        
            x2 = node.x
            step = (x2 - x1) / float(nlosses + 1)
            
            for x in util.frange(x1 + step, x2-(step/2.0), step):
                losses.append(lines(x, node.y - .2, x, node.y + .2))
        
        return group(group(*dups), group(*losses))


    def setMode(self, mode):
        print "mode is now '%s'" % mode
        self.mode = mode
        

    def nodeClick(self, node):
        """Node click callback"""
        
        if self.mode == "gene":
            # print gene names
            sumtree.SumTree.nodeClick(self, node)
        elif self.mode == "events":
            self.printEvents(node)
        elif self.mode == "reroot":
            self.reroot(node)
    
    
    def printEvents(self, node):
        """Prints the events that occur on a node"""
        
        print "-" * 20
        print "%s (%.3f sub/site):" % (node.name, node.dist),
        
        if self.events:
            if self.events[node] == "dup":
                print "duplication"
            elif self.events[node] == "spec":
                print "speciation"
            elif self.events[node] == "gene":
                print "extant"
            
            losses = util.groupby(lambda x: x[0], self.losses)
            
            if node in losses:
                print len(losses[node]), "gene losses"
                for i, (node, schild) in enumerate(losses[node]):
                    print "loss %d in species %s" % (i+1, str(schild.name))
                    
                    for sleaf in schild.leafNames():
                        print "  %s" % sleaf
            
        else:
            print "no reconciliation available"
            
        
    def reroot(self, node):
        try:
            treelib.reroot(self.tree, node.name, newCopy=False)
        except e:
            print e
        print "rerooted on node", node.name
        self.recon = None
        self.setupRecon()
        
        self.show()
        