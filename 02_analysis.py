import pandas as pd, numpy as np
pd.set_option('display.width',200)
raw=pd.read_pickle('all.pkl')
n0=len(raw)
df=raw.drop_duplicates(); n1=len(df)
START,END=pd.Timestamp('2016-02-03'),pd.Timestamp('2016-03-14')
df=df[(df.BoxTime>=START)&(df.BoxTime<END)].copy(); n2=len(df)
for c in ['Duration','RealTimePlaying','ElapsedTimePlaying']: df[c]=pd.to_numeric(df[c],errors='coerce')
df['date']=df.BoxTime.dt.date; df['hour']=df.BoxTime.dt.hour; df['dow']=df.BoxTime.dt.dayofweek
print('rows raw/dedup/window',n0,n1,n2)

# ---- live TV views
ch=df[df.Event=='StopChannel'].copy()
ch=ch[(ch.Duration>=0)&(ch.Duration<=12*3600)]   # bỏ >12h (hộp bật quên tắt)
ch['secs']=ch.Duration
ch['bucket']=pd.cut(ch.secs,[-1,10,300,1800,1e9],labels=['Zapping (<=10s)','Ngắn (10s-5p)','Vừa (5-30p)','Dài (>30p)'])
# ---- VOD views
vd=df[df.Event=='StopVOD'].copy()
vd=vd[(vd.RealTimePlaying>0)&(vd.RealTimePlaying<=12*3600)]
vd['secs']=vd.RealTimePlaying
vd['completion']=(vd.ElapsedTimePlaying/vd.Duration).clip(0,1)

kpi={}
kpi['Số dòng log thô']=n0; kpi['Sau khi bỏ trùng']=n1; kpi['Trong cửa sổ phân tích (03/02-13/03/2016)']=n2
kpi['Số hộp (MAC) hoạt động']=df.Mac.nunique(); kpi['Số hợp đồng']=df.Contract.nunique()
kpi['Giờ xem TV trực tiếp']=round(ch.secs.sum()/3600); kpi['Giờ xem VOD']=round(vd.secs.sum()/3600)
kpi['Lượt xem TV']=len(ch); kpi['Lượt xem VOD']=len(vd)
kpi['% lượt TV là zapping (<=10s)']=round((ch.secs<=10).mean()*100,1)
kpi['% giờ xem là TV']=round(ch.secs.sum()/(ch.secs.sum()+vd.secs.sum())*100,1)
kpi['Số hộp có xem VOD']=vd.Mac.nunique(); kpi['Số hộp có xem TV']=ch.Mac.nunique()
for k,v in kpi.items(): print(k,v)

# ---- time patterns
hrs=pd.concat([ch[['hour','dow','secs']].assign(t='TV'),vd[['hour','dow','secs']].assign(t='VOD')])
heat=hrs[hrs.t=='TV'].pivot_table(index='dow',columns='hour',values='secs',aggfunc='sum',fill_value=0)/3600
hour_t=hrs.pivot_table(index='hour',columns='t',values='secs',aggfunc='sum',fill_value=0)/3600
print(hour_t.round(0).T.to_string())
dow_t=hrs.pivot_table(index='dow',columns='t',values='secs',aggfunc='sum',fill_value=0)/3600
print(dow_t.round(0))

# ---- channels
g=ch.groupby('ItemName').agg(views=('secs','size'),hours=('secs',lambda s:s.sum()/3600),boxes=('Mac','nunique'),
    zap=('secs',lambda s:(s<=10).mean()),med=('secs','median'))
g['avg_min_per_view']=g.hours*60/g.views
top=g.sort_values('hours',ascending=False).head(15)
print(top.round(2))
print(g[g.views>=1000].sort_values('zap',ascending=False).head(8).round(2))
print(g[g.views>=1000].sort_values('zap').head(8).round(2))

# ---- VOD content
vt=vd.groupby('ItemName').agg(plays=('secs','size'),hours=('secs',lambda s:s.sum()/3600),boxes=('Mac','nunique'),compl=('completion','mean'))
print(vt.sort_values('hours',ascending=False).head(12).round(2))
vc=vd.groupby('PublishCountry').agg(plays=('secs','size'),hours=('secs',lambda s:s.sum()/3600),boxes=('Mac','nunique'))
print(vc.sort_values('hours',ascending=False).head(8).round(1))

# ---- VOD funnel (distinct boxes-sessions)
fun=['EnterVOD','EnterFolderVOD','EnterDetailVOD','StartVOD','StopVOD']
f=df[df.Event.isin(fun)].groupby('Event').Session.nunique().reindex(fun); print(f)
f2=df[df.Event.isin(fun)].groupby('Event').Mac.nunique().reindex(fun); print(f2)

# ---- feature adoption
feat={'Timeshift':'StartTimeshift','EPG':'ShowEPG','Lịch phát sóng':'Show schedule','Yêu thích (kênh/VOD)':'InsertFavorite','Báo nhắc':'SetAlarm','PiP':'PiPSwitch','Tìm kiếm VOD':'SearchVOD'}
allm=df.Mac.nunique()
ad={k:df[df.Event==e].Mac.nunique()/allm*100 for k,e in feat.items()}
print({k:round(v,1) for k,v in ad.items()})
drm=df[df.Event.isin(['GetDRMKeySuccessful','GetDRMKeyFailed'])].Event.value_counts(); print(drm)

# ---- per-box table + tenure
box=pd.DataFrame({'tv_h':ch.groupby('Mac').secs.sum()/3600,'vod_h':vd.groupby('Mac').secs.sum()/3600,
  'tv_views':ch.groupby('Mac').size(),'zap':ch.groupby('Mac').secs.apply(lambda s:(s<=10).mean())})
box['active_days']=df.groupby('Mac').date.nunique()
box=box.reindex(df.Mac.unique()).fillna({'tv_h':0,'vod_h':0,'tv_views':0}); box['active_days']=df.groupby('Mac').date.nunique()
box['total_h']=box.tv_h+box.vod_h
box['h_per_active_day']=box.total_h/box.active_days
u=pd.read_csv('/mnt/user-data/uploads/user_info.txt',sep='\t'); u.columns=['MAC','tenure_days']; u['Mac']=u.MAC.str.replace('FBOX','',regex=False)
box=box.reset_index().rename(columns={'index':'Mac'}).merge(u[['Mac','tenure_days']],on='Mac',how='left')
print('tenure matched',box.tenure_days.notna().mean())
box['tenure_band']=pd.cut(box.tenure_days,[-1,90,180,365,1e5],labels=['<3 tháng','3-6 tháng','6-12 tháng','>12 tháng'])
tb=box.groupby('tenure_band',observed=True).agg(boxes=('Mac','size'),active_days=('active_days','mean'),total_h=('total_h','mean'),vod_h=('vod_h','mean'),zap=('zap','mean'))
print(tb.round(2)); print(box[['tenure_days','total_h','active_days','vod_h']].corr(method='spearman').round(2))
# segments
q=box.total_h
box['segment']=pd.cut(q,[-1,0,box.total_h[box.total_h>0].quantile(.5),box.total_h[box.total_h>0].quantile(.9),1e9],labels=['Không xem','Nhẹ (50% dưới)','Trung bình (50-90%)','Nặng (top 10%)'])
sg=box.groupby('segment',observed=True).agg(boxes=('Mac','size'),hours=('total_h','sum'),vod_share=('vod_h','sum'))
sg['hours_share%']=sg.hours/sg.hours.sum()*100; print(sg.round(1))
box['vod_ratio']=box.vod_h/box.total_h.replace(0,np.nan)
box['type']=np.select([box.total_h==0,box.vod_ratio>=.5,box.vod_ratio.between(.1,.5,inclusive='left')],['Không xem','Mê VOD (>=50% giờ là VOD)','Pha trộn'],'Chủ yếu TV (<10% VOD)')
print(box.type.value_counts())
print(box.groupby('type').agg(n=('Mac','size'),total_h=('total_h','mean'),days=('active_days','mean'),ten=('tenure_days','mean')).round(1))

import pickle
pickle.dump(dict(kpi=kpi,heat=heat,hour_t=hour_t,dow_t=dow_t,top=top,g=g,vt=vt,vc=vc,f=f,f2=f2,ad=ad,tb=tb,sg=sg,drm=drm),open('out/res.pkl','wb'))
box.to_pickle('out/box.pkl'); ch.to_pickle('out/ch.pkl'); vd.to_pickle('out/vd.pkl')
