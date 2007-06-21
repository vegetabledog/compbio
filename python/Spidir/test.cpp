/*=============================================================================

    Test SPIDIR functions

=============================================================================*/


#include <stdlib.h>
#include <stdio.h>
#include <string>

#include "common.h"
#include "parsimony.h"
#include "search.h"
#include "Matrix.h"
#include "Tree.h"


using namespace std;


int main(int argc, char **argv)
{

    // read sequences
    Sequences *aln = readAlignFasta(argv[1]);
    writeFasta("out.fa", aln);
    assert(checkSequences(aln->nseqs, aln->seqlen, aln->seqs));
    
    // calc distmatrix
    Matrix<float> distmat(aln->nseqs, aln->nseqs);
    calcDistMatrix(aln->nseqs, aln->seqlen, aln->seqs, 
                   distmat);
    
    // write dist matrix
    if (argc > 2)
        writeDistMatrix(argv[2], aln->nseqs, distmat, aln->names);
    
    
    // do neighbor joining
    int nnodes = aln->nseqs * 2 - 1;
    Tree tree(nnodes);    
    ExtendArray<int> ptree(nnodes);
    ExtendArray<float> dists(nnodes);
    
    neighborjoin(aln->nseqs, distmat, ptree, dists);
    ptree2tree(nnodes, ptree, &tree);
    parsimony(&tree, aln->nseqs, aln->seqs);
    
    for (int i=0; i<100; i++) {
        Node *node = tree.root;
        while (node->parent == NULL || node->name < aln->nseqs)
            node = tree.nodes[int(rand() / float(RAND_MAX) * tree.nnodes)];
        proposeNni(&tree, node, node->parent, int(rand() / float(RAND_MAX) * 2));
        
        parsimony(&tree, aln->nseqs, aln->seqs);
        //printTree(&tree);
    }
}