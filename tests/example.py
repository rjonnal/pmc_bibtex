import sys
from pmc_bibtex import ArticleList

alist = ArticleList()
query = '(adaptive+optics)+AND+(optical+coherence+tomography)'
alist.build(query)
alist.to_bibtex('test.bib')
sys.exit()

bibtex_fid = open('pmc_aooct.bib','wb')

with open('aooct_citations.csv','wb') as f:
    writer = csv.writer(f)
    for id in idlist:
        id = id[4:-5]
        print id
        xml = fetch(id)
        art = xml2article(xml)
        match = art.conjoint_search(['adaptive optics','optical coherence tomography'])
        include_fn = os.path.join('.','xml','%s.xml.include'%id)
        
        if not match:
            include_fid = open(include_fn,'wb')
            include_fid.write('0')
            include_fid.close()
            print 'No match.'
            continue
        try:
            include_fid = open(include_fn,'rb')
            include = bool(include_fid.read())
            include_fid.close()
            if include:
                art.to_csv(writer)
                bibtex_fid.write(art.to_bibtex()+'\n\n')
        except Exception:
            print
            print art.to_list()
            print art.abstract.replace('\n',' ')
            ans = raw_input('Include? ')
            include = ans.lower()=='y'
            include_fid = open(include_fn,'wb')
            if include:
                include_fid.write('1')
                art.to_csv(writer)
                bibtex_fid.write(art.to_bibtex()+'\n\n')
            else:
                include_fid.write('0')
            include_fid.close()

bibtex_fid.close()
