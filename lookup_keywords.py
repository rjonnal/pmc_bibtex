fid = open('arvo_keywords.txt','rb')
textlist = fid.readlines()
fid.close()

query_list = []

for item in textlist:
    item = item.strip()
    item = item.replace(':','')
    q = 'TS=(%s)'%item
    query_list.append(q)
        
