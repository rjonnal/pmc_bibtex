from pmc_bibtex import ArticleList
from matplotlib import pyplot as plt
import numpy as np

alist = ArticleList()
query = '(adaptive+optics)'
alist.build(query,retmax=10000)
years = []
bins = np.arange(2003.5,2015.6,1.0)

for a in alist.article_list:
    y = 2016
    for key in a.date_dict.keys():
        y_c = a.date_dict[key].year
        if y_c<y:
            y = y_c
    if 2004<=y<=2015: years.append(y)
plt.hist(years,bins)
plt.show()
