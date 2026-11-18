import ast, glob, os, pandas as pd
keep=['Event','AppName','AppId','ItemId','ItemName','Mac','CustomerID','Contract','BoxTime','Duration','RealTimePlaying','ElapsedTimePlaying','Screen','LogId','Session','PublishCountry','Directors','Folder','SubMenuId','ChapterID','Key','isLandingPage','ip_wan']
os.makedirs('parts',exist_ok=True)
for f in sorted(glob.glob('/mnt/user-data/uploads/logt*.txt')):
    rows=[];bad=0
    with open(f,encoding='utf-8',errors='replace') as fh:
        for line in fh:
            line=line.strip()
            if not line: continue
            try: d=ast.literal_eval(line)
            except Exception: bad+=1; continue
            rows.append({k:d.get(k) for k in keep})
    df=pd.DataFrame(rows); df['src']=os.path.basename(f)[:-4]
    df.to_pickle(f'parts/{df.src.iloc[0]}.pkl')
    print(f,len(df),'bad',bad,flush=True)
    del rows,df
