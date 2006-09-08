
# python libs
import os

# rasmus libs
import phylip
import util
import alignlib


def dndsMatrix(seqs, saveOutput="", verbose=False, safe=True):
    
    if safe:
        seqs = alignlib.mapalign(seqs, valfunc=removeStopCodons)
    
    phylip.validateSeq(seqs)
    cwd = phylip.createTempDir()

    util.tic("yn00 on %d of length %d" % (len(seqs), len(seqs.values()[0])))

    # create input
    labels = phylip.fasta2phylip(file("seqfile.phylip", "w"), seqs)
    util.writeVector(file("labels", "w"), labels)    
    
    # create control file
    out = file("yn00.ctl", "w")
    print >>out, "seqfile = seqfile.phylip"
    print >>out, "outfile = outfile"
    out.close()
    
    # run phylip
    if verbose:
        os.system("yn00 yn00.ctl")
    else:
        os.system("yn00 yn00.ctl > /dev/null")
    
    try:
        dnmat = phylip.readDistMatrix("2YN.dN")
        dsmat = phylip.readDistMatrix("2YN.dS")
    except:
        # could not make distance matrix
        if safe:
            # make dummy matrix
            dnmat = labels, [[0] * len(labels)] * len(labels)
            dsmat = labels, [[0] * len(labels)] * len(labels)
        else:
            raise Exception("could not read dn or ds matrices")
    
    if saveOutput != "":
        phylip.saveTempDir(cwd, saveOutput)
    else:
        phylip.cleanupTempDir(cwd)
    
    util.toc()
    
    return dnmat, dsmat



def removeStopCodons(seq):
    assert len(seq) % 3 == 0
    
    seq2 = []
    
    for i in range(0, len(seq), 3):
        codon = seq[i:i+3].upper()
        if alignlib.translate(codon) == "*":
            seq2.append("NNN")
        else:
            seq2.append(codon)
    return "".join(seq2)

