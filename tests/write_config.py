import ConfigParser

config = ConfigParser.RawConfigParser()

# When adding sections or items, add them in the reverse order of
# how you want them to be displayed in the actual file.
# In addition, please note that using RawConfigParser's and the raw
# mode of ConfigParser's respective set functions, you can assign
# non-string values to keys internally, but will receive an error
# when attempting to write to a file or when you get it in non-raw
# mode. SafeConfigParser does not allow such assignments to take place.
config.add_section('PubMed')
config.set('PubMed','user_email','me@myuniversity.edu')
config.set('PubMed','user_tool','biopython')
config.add_section('Paths')
config.set('Paths', 'title_key_file', './bib/longtitles.bib')
config.set('Paths', 'cache_root_directory', '/home/rjonnal/code/pmc_bibtex/.cache/')
config.add_section('Constants')
config.set('Constants', 'unknown_affiliation','unknown affiliation')



# Writing our configuration file to 'example.cfg'
with open('pmc_bibtex.cfg', 'wb') as configfile:
    config.write(configfile)
