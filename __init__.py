from Bio import Entrez
from bs4 import BeautifulSoup as Soup
import sys,os,csv
import datetime
import ConfigParser
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = ConfigParser.RawConfigParser()
config.read('pmc_bibtex.cfg')

def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def ascii_encode(s):
    return s.encode('ascii','xmlcharrefreplace')

def MySoup(argin):
    return Soup(argin,"html.parser")

journal_dict = {}

try:
    title_key_file = config.get('Paths','title_key_file')
    fid = open(title_key_file,'rb')
    temp = fid.read()
    fid.close()
    temp = temp.strip()
    temp = temp.split('@string')
    for item in temp:
        item = item.strip()
        if len(item)>5:
            if item[0]=='{' and item[-1]=='}':
                pair = item[1:-1]
                value,key = pair.split('=')
                key = key.replace('"','')
                journal_dict[key.lower()] = value
except:
    pass

try:
    cache_root_directory = config.get('Paths', 'cache_root_directory')
except:
    cache_root_directory = './.cache'

try:
    logger.info('Creating %s.'%cache_root_directory)
    os.makedirs(cache_root_directory)
except OSError as e:
    logger.info('%s exists.'%cache_root_directory)

class Author:
    def __init__(self,surname,given_name,aff_tag=''):
        self.surname = surname
        self.given_name = given_name
        self.affiliation = 'no_affiliation'
        self.aff_tag = aff_tag
        
    def __str__(self):
        s = '%s, %s (%s)'%(self.surname,self.given_name,self.affiliation)
        return ascii_encode(s)

    def __repr__(self):
        s = '%s, %s (%s)'%(self.surname,self.given_name,self.affiliation)
        return ascii_encode(s)


class Article:
    def __init__(self,title,author_list,journal,date_dict,keyword_list,abstract,id_dict,pages,volume,issue):
        self.title = title
        self.author_list = author_list
        self.journal = journal
        self.date_dict = date_dict
        self.keyword_list = keyword_list
        self.abstract = abstract
        self.id_dict = id_dict
        self.pages = pages
        self.volume = volume
        self.issue = issue
        
        ambiguous_terms = ['a','an','in','to','the','on']

        try:
            title_list = self.title.replace('-',' ').lower().split(' ')
            tag_word = title_list[0]
            while title_list[0] in ambiguous_terms:
                tag_word = tag_word + title_list[1]
                title_list = title_list[1:]
            self.tag = self.author_list[0].surname.lower().replace(' ','') + '%s'%(self.get_year()) + tag_word
        except Exception as e:
            self.tag = 'no_tag'

    def keyword_has(self,term):
        term = term.lower()
        return term in self.keyword_list

    def abstract_has(self,term):
        return self.abstract.find(term.lower())>-1

    def title_has(self,term):
        return self.title.lower().find(term.lower())>-1

    def conjoint_search(self,search_terms):
        match = True
        for search_term in search_terms:
            term_match = self.abstract_has(search_term) or self.keyword_has(search_term) or self.title_has(search_term)
            match = match and term_match
            if not match: break
        return match

    def to_bibtex(self):
        authors = '%s, %s '%(self.author_list[0].surname, self.author_list[0].given_name)
        for author in self.author_list[1:]:
            authors = authors + 'AND %s, %s '%(author.surname, author.given_name)
        authors = authors.strip()
        journal = self.journal
        try:
            journal = journal_dict[journal.lower()]
        except Exception as e:
            pass
        strings = (self.tag,self.title,journal,authors,self.pages,self.volume,self.issue,self.get_year())
        out = '@article{%s,\n\ttitle={%s},\n\tjournal={%s},\n\tauthor={%s},\n\tpages={%s},\n\tvolume={%s},\n\tissue={%s},\n\tyear={%s}}'%strings
        return ascii_encode(out)

    def to_list(self):
        def outappend(amb_string):
            out.append(ascii_encode(amb_string))
            
        out = []
        outappend(self.tag)
        outappend(self.title)
        temp = ''
        for author in self.author_list:
            temp = temp + author.surname+', '
        temp = temp[:-2]
        outappend(temp)
        outappend(self.journal)
        outappend(u'%s'%(self.get_year()))
        outappend(self.id_dict['pmc'])
        outappend('http://www.ncbi.nlm.nih.gov/pmc/articles/PMC%s'%(self.id_dict['pmc']))
        return out

    def to_csv(self,csv_writer):
        out = self.to_list()
        csv_writer.writerow(out)
        
    
    def __str__(self):
        s = self.title + '; '
        for author in self.author_list:
            s = s + author.surname + ', '
        s = s[:-2] + '; pmc %s'%(self.id_dict['pmc']) + '; %s'%(self.journal) + '; %d;'%(self.get_year())
        return ascii_encode(s)

    def __repr__(self):
        s = self.title + '; '
        for author in self.author_list:
            s = s + author.surname + ', '
        s = s[:-2] + '; pmc %s'%(self.id_dict['pmc']) + '; %s'%(self.journal) + '; %d;'%(self.get_year())
        return ascii_encode(s)

    def get_year(self):
        earliest = 1e10
        for key in self.date_dict.keys():
            if int(self.date_dict[key].year)<earliest:
                earliest = int(self.date_dict[key].year)
                
        return '%d'%earliest

def xml2article(xml):
    out = []
    soup = MySoup(xml)
    articles = soup.findAll('article')
    for article in articles:
        # determine the article title
        title_list = article.findAll('article-title')
        a_title = title_list[0].get_text()

        # determine the journal
        journal_list = article.findAll('journal-title')
        a_journal = journal_list[0].get_text()

        # determine the DOI, pmc, pmid
        id_dict = {}
        articleid_list = article.findAll('article-id')
        for articleid in articleid_list:
            key = articleid.attrs['pub-id-type']
            value = articleid.get_text()
            id_dict[key] = value

        # determine the date of publication
        # there are numerous dates; keep track of their attributes:
        a_date_dict = {}
        pubdate_list = article.findAll('pub-date')
        for pubdate in pubdate_list:
            key = pubdate.attrs['pub-type']
            try: year = int(pubdate.find('year').get_text())
            except Exception: year = 0
            try: month = int(pubdate.find('month').get_text())
            except Exception: month = 1
            try: day = int(pubdate.find('day').get_text())
            except Exception: day = 1
            a_date_dict[key] = datetime.date(year,month,day)


        # determine the pages
        try:
            fpage = article.findAll('fpage')[0].get_text()
            lpage = article.findAll('lpage')[0].get_text()
            pages = '%s--%s'%(fpage,lpage)
        except Exception:
            pages = ''
            
        # determine the volume and issue
        try:
            volume = article.findAll('volume')[0].get_text()
        except Exception:
            volume = '-1'
        try:
            issue = article.findAll('issue')[0].get_text()
        except Exception:
            issue = '-1'
            
        # determine the authors, contained in <contrib> block
        contrib_list = article.findAll('contrib')
        a_author_list = []
        for contrib in contrib_list:
            name_list = contrib.findAll('name')
            xref_list = contrib.findAll('xref')

            # determine this author's first and last names
            for name in name_list:
                s_soup = name.findAll('surname')
                g_soup = name.findAll('given-names')
                surname = s_soup[0].contents[0]
                given_name = g_soup[0].contents[0]

            # determine the XML code (contained in the 'rid' attribute
            # of the <xref> tag) that's a key for affiliation lookup
            aff_tag = ''
            for xref in xref_list:
                xref_attrs = xref.attrs
                if xref_attrs['ref-type']=='aff':
                    try:
                        aff_tag = xref_attrs['rid']
                    except Exception as e:
                        aff_tag = ''
                
            author = Author(surname,given_name,aff_tag)
            # append the author to the author list, even though we
            # only have the author's affiliation key, not the actual
            # affiliation text, which we'll fill in later:
            a_author_list.append(author)
            
        # now make a dictionary in which the authors' affiliation keys
        # can be used to look up their affiliations
        affiliation_list = article.findAll('aff')
        affiliation_dictionary = {}
        affiliation_dictionary[''] = UNKNOWN_AFFILIATION
        for affiliation in affiliation_list:
            if len(affiliation.contents[0])>5:
                affiliation_contents = affiliation.contents[0]
            else:
                try:
                    affiliation_contents = affiliation.findAll('addr-line')[0].contents[0]
                except Exception as e:
                    affiliation_contents = UNKNOWN_AFFILIATION
            aff_tag_dict = dict(affiliation.attrs)
            try:
                aff_tag = aff_tag_dict['id']
            except Exception:
                aff_tag = ''
            affiliation_dictionary[aff_tag] = affiliation_contents

        # now we can set the affiliation text for each author, using our dictionary:
        for author in a_author_list:
            try:
                author.affiliation = affiliation_dictionary[author.aff_tag]
            except Exception:
                author.affiliation = UNKNOWN_AFFILIATION
        # now let's get the abstract and keywords:
        abstract_list = article.findAll('abstract')
        candidates = []
        a_abstract = ''
        for abstract in abstract_list:
            a_abstract = a_abstract + '\n' + abstract.get_text()

        keyword_list = article.findAll('kwd')
        a_keyword_list = []
        for kw in keyword_list:
            # make all keywords lower case, just because
            a_keyword_list.append(kw.get_text().lower())

        art = Article(a_title,a_author_list,a_journal,a_date_dict,a_keyword_list,a_abstract,id_dict,pages,volume,issue)
        out.append(art)
    return out

def term_to_directory(term):
    out = term
    replacements = [
        ['(','_closeparen_'],
        [')','_openparen_'],
        ['+','_plus_']
        ]
    for r in replacements:
        out = out.replace(r[0],r[1])
    return out
        

def search(term,retmax=1000):
    """Searches Pub Med Central for TERM and returns a list, not longer than RETMAX, of PMCID numbers."""
    term_cache = os.path.join(cache_root_directory,term_to_directory(term))
    try:
        os.makedirs(term_cache)
    except:
        pass
    idfn = os.path.join(term_cache,'idlist.txt')
    print idfn
    try:
        ids_fid = open(idfn,'rb')
        ids = ids_fid.read()
        ids_fid.close()
    except Exception:
        Entrez.email = config.get('PubMed','user_email')
        Entrez.tool = config.get('PubMed','user_tool')
        retmax = 1000
        handle = Entrez.esearch(db='pmc',term=term,retmax=retmax)
        ids = handle.read()
        handle.close()
        ids_fid = open(idfn,'wb')
        ids_fid.write(ids)
        ids_fid.close()

    idlist = ids.split('<IdList>')[1].split('</IdList>')[0].split('\n')[1:-1]
    return idlist

search(term='(adaptive+optics)+AND+(optical+coherence+tomography)',retmax=10)
sys.exit()


def fetch(id):
    term_cache = os.path.join(cache_root_directory,term_to_directory(term))
    if not os.path.exists(term_cache):
        os.makedirs(term_cache)
        
    fn = os.path.join(term_cache,'%s.xml'%id)
    try:
        fid = open(fn,'r')
        xml = fid.read()
        fid.close()
        print 'fetching from cache'
    except Exception as e:
        handle = Entrez.efetch(db='pmc',id=id)
        xml = handle.read()
        handle.close()
        fid = open(fn,'w')
        fid.write(xml)
        fid.close()
        print 'fetching from PMC'
    return xml


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