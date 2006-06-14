
"""
GTF file format
http://genes.cse.wustl.edu/GTF22.html

<seqname> <source> <feature> <start> <end> <score> <strand> <frame> [attributes] [comments]

The following feature types are required: "CDS", "start_codon", "stop_codon".
The features "5UTR", "3UTR", "inter", "inter_CNS", "intron_CNS" and "exon" are
optional. All other features will be ignored. The types must have the correct
capitalization shown here.

<start> <end> 
Integer start and end coordinates of the feature relative to the
beginning of the sequence named in <seqname>.  <start> must be less than or equal
to <end>. Sequence numbering starts at 1. Values of <start> and <end> that extend
outside the reference sequence are technically acceptable, but they are
discouraged.

<score> 
The score field indicates a degree of confidence in the feature's
existence and coordinates. The value of this field has no global scale but may
have relative significance when the <source> field indicates the prediction
program used to create this annotation. It may be a floating point number or
integer, and not necessary and may be replaced with a dot.

<frame> 
0 indicates that the feature begins with a whole codon at the 5' most
base. 1 means that there is one extra base (the third base of a codon) before the
first whole codon and 2 means that there are two extra bases (the second and
third bases of the codon) before the first codon. Note that for reverse strand
features, the 5' most base is the <end> coordinate.
"""

import util
import algorithms


TEST_GTF = \
"""
140\tTwinscan\tinter\t5141\t8522\t.\t-\t.\tgene_id ""; transcript_id "";
140\tTwinscan\tinter_CNS\t8523\t9711\t.\t-\t.\tgene_id ""; transcript_id "";
"""


class Region:
    def __init__(self):
        pass
    
    
    def set(self,
            seqname="", 
            source="",
            feature="",
            start=0,
            end=0,
            score=None,
            strand=1,
            frame=None,
            attrs=None,
            comment=""):
        self.seqname = seqname
        self.source  = source
        self.feature = feature
        self.start   = start
        self.end     = end
        self.score   = score
        self.strand  = strand
        self.frame   = frame

        if attrs == None:
            self.attrs = {}
        else:
            self.attrs = attrs

        self.comment = comment        

    
    def __str__(self):
        if self.score == None:
            score = "."
        else:
            score = str(self.score)
        
        if self.strand == None:
            strand = "."
        elif self.strand == 1:
            strand = "+"
        else:
            strand = "-"
        
        if self.frame == None:
            frame = "."
        else:
            frame = str(self.frame)
        
        attrs = []
        for key, val in self.attrs.items():
            attrs.append('%s "%s";' % (key, str(val)))
        attr = " ".join(attrs)
        
        if self.comment != "":
            comment = " #%s" % self.comment
        else:
            comment = ""
        
        
        return "%s\t%s\t%s\t%d\t%d\t%s\t%s\t%s\t%s%s" % \
            (self.seqname, 
             self.source, 
             self.feature,
             self.start,
             self.end,
             score,
             strand,
             frame,
             attr,
             comment)
    
    
    def __repr__(self):
        return self.__str__()



class RegionIter:
    """An iterator that walks down a sorted list of regions"""

    def __init__(self, regions, start, end, index=None):
        self.regions  = regions
        self.start  = start
        self.end    = end
        self.nregions = len(regions)
        
        if index != None:
            self.index = index
        else:
            self.index = 0
            
            # find starting index by binary search
            low, top = algorithms.binsearch(regions, start-1, 
                                            lambda a,b: cmp(a.start, b))
            
            if top != None:
                self.index = top
            else:
                self.index = self.nregions
    
    def __iter__(self):
        return self
    
    
    def next(self):
        if (self.index < self.nregions) and \
           (self.regions[self.index].start < self.end):
            gene = self.regions[self.index]
        else:
            raise StopIteration
        
        self.index += 1
        return gene
    
    

def readGffRegion(line):
    region = Region()

    if "#" in line:
        pos = line.index("#")
        region.comment = line[pos+1:]
        line = line[:pos]
    else:
        region.comment = ""

    tokens = line.split("\t")

    region.seqname = tokens[0]
    region.source  = tokens[1]
    region.feature = tokens[2]
    region.start   = int(tokens[3])
    region.end     = int(tokens[4])
    if tokens[5] == ".":
        region.score = None
    else:
        region.score = float(tokens[5])
    if tokens[6] == "+":
        region.strand = 1
    else:
        region.strand = -1
    if tokens[7] == ".":
        region.frame = None
    else:
        region.frame = int(tokens[7])
    region.attrs = readGffAttrs(tokens[8])

    return region


def readGffAttrs(attrstr):
    tokens = attrstr.split(";")
    attrs = {}

    for attr in tokens[:-1]:
        attr = attr.strip()

        pos = attr.index(" ")

        key = attr[:pos]
        val = attr[pos+1:].split("\"")[1]

        attrs[key] = val

    return attrs


def readGff(filename):
    infile = util.openStream(filename)
    
    regions = []
    
    for line in infile:
        line = line.rstrip()
        if len(line) == 0 or line[0] == "#":
            continue
        regions.append(readGffRegion(line))
    
    return regions


def writeGff(filename, regions):
    out = util.openStream(filename, "w")
    
    for region in regions:
        print >>out, region

def iterGff(filename):
    infile = util.openStream(filename)
    
    for line in infile:
        line = line.rstrip()
        print line
        if len(line) == 0 or line[0] == "#":
            continue
        yield readGffRegion(line)



if __name__ == "__main__":
    from rasmus.common import *
    
    pc(readGff(strStream(TEST_GTF)))
