import sys
from pmc_bibtex import ArticleList

alist = ArticleList()
query = '(adaptive+optics)+AND+(optical+coherence+tomography)'
alist.build(query)
alist.to_bibtex('test.bib')
