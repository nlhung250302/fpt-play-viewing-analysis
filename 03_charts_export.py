import pickle, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'font.size':10})
R=pickle.load(open('out/res.pkl','rb')); box=pd.read_pickle('out/box.pkl'); ch=pd.read_pickle('out/ch.pkl'); vd=pd.read_pickle('out/vd.pkl')
B,O,G='#1f6feb','#f28e2b','#8c8c8c'
def p1(ax):
    h=R['hour_t']; ax.plot(h.index,h.TV,color=B,lw=2.5,label='TV trực tiếp'); ax.plot(h.index,h.VOD,color=O,lw=2.5,label='VOD')
    ax.axvspan(19.5,22.5,color='#ffe9b3',alpha=.5); ax.set_xticks(range(0,24,3)); ax.set_title('1. Giờ nào cả nước xem nhiều nhất?\n(tổng giờ xem theo giờ trong ngày)',loc='left',fontweight='bold'); ax.set_xlabel('Giờ trong ngày'); ax.set_ylabel('Giờ xem'); ax.legend(frameon=False)
def p2(ax):
    top=R['top'].head(10).iloc[::-1]; c=[O if z>.35 else B for z in top.zap]
    ax.barh(top.index,top.hours,color=c); ax.set_title('2. Top 10 kênh theo giờ xem\n(cam = tỉ lệ lướt qua <=10s trên 35%)',loc='left',fontweight='bold'); ax.set_xlabel('Giờ xem')
def p3(ax):
    t=R['vt'].sort_values('hours',ascending=False).head(10).iloc[::-1]; ax.barh([s[:28] for s in t.index],t.hours,color=B); ax.set_title('3. Top 10 phim VOD theo giờ xem',loc='left',fontweight='bold'); ax.set_xlabel('Giờ xem')
def p4(ax):
    a=pd.Series(R['ad']).sort_values(); ax.barh(a.index,a.values,color=B)
    for i,v in enumerate(a.values): ax.text(v+.5,i,f'{v:.0f}%',va='center')
    ax.set_title('4. % hộp từng dùng mỗi tính năng',loc='left',fontweight='bold'); ax.set_xlim(0,50)
def p5(ax):
    t=R['tb']; x=np.arange(len(t)); ax.bar(x-.2,t.vod_h,.4,color=O,label='Giờ VOD TB/hộp'); ax.set_xticks(x); ax.set_xticklabels(t.index); ax.set_ylabel('Giờ VOD')
    a2=ax.twinx(); a2.plot(x+.2,t.zap*100,'o-',color=B,label='% zapping'); a2.set_ylabel('% lượt TV zapping'); a2.spines['top'].set_visible(False); a2.set_ylim(0,60)
    ax.set_title('5. Khách mới xem VOD ít hơn, lướt kênh nhiều hơn',loc='left',fontweight='bold')
def p6(ax):
    s=box.type.value_counts().drop('Không xem',errors='ignore'); ax.pie(s.values,labels=[f'{k}\n{v} hộp' for k,v in s.items()],colors=[B,G,O],startangle=90,wedgeprops=dict(width=.45)); ax.set_title('6. Ba kiểu khách hàng',loc='left',fontweight='bold')
fs=[p1,p2,p3,p4,p5,p6]
fig,axs=plt.subplots(3,2,figsize=(15,15)); 
for f,a in zip(fs,axs.ravel()): f(a)
fig.suptitle('FPT Play Box – Hành vi xem (03/02–13/03/2016, 1.690 hộp)',fontsize=16,fontweight='bold',x=.05,ha='left'); fig.tight_layout(rect=[0,0,1,.97]); fig.savefig('out/dashboard.png',dpi=110); plt.close()
# heatmap
fig,ax=plt.subplots(figsize=(11,3.8)); h=R['heat']; im=ax.imshow(h.values,aspect='auto',cmap='YlOrRd'); ax.set_yticks(range(7)); ax.set_yticklabels(['T2','T3','T4','T5','T6','T7','CN']); ax.set_xticks(range(0,24,2)); ax.set_xlabel('Giờ'); ax.set_title('Heatmap giờ xem TV: thứ x giờ',loc='left',fontweight='bold'); plt.colorbar(im,label='Giờ xem'); fig.tight_layout(); fig.savefig('out/heatmap_tv.png',dpi=110); plt.close()
# Excel
k=pd.DataFrame(list(R['kpi'].items()),columns=['Chỉ số','Giá trị'])
ch_t=R['g'][R['g'].views>=500].sort_values('hours',ascending=False).reset_index().rename(columns={'ItemName':'Kênh','views':'Lượt xem','hours':'Giờ xem','boxes':'Số hộp','zap':'Tỉ lệ zapping','med':'Median giây/lượt','avg_min_per_view':'Phút TB/lượt'})
vt=R['vt'].sort_values('hours',ascending=False).head(100).reset_index().rename(columns={'ItemName':'Phim','plays':'Lượt play','hours':'Giờ xem','boxes':'Số hộp','compl':'Tỉ lệ xem hết TB'})
vc=R['vc'].sort_values('hours',ascending=False).reset_index().rename(columns={'PublishCountry':'Nước sản xuất','plays':'Lượt play','hours':'Giờ xem','boxes':'Số hộp'})
vc['Phút/lượt']=vc['Giờ xem']*60/vc['Lượt play']
hr=R['hour_t'].reset_index().rename(columns={'hour':'Giờ','TV':'Giờ xem TV','VOD':'Giờ xem VOD'})
ad=pd.DataFrame({'Tính năng':list(R['ad']),'% hộp từng dùng':[round(v,1) for v in R['ad'].values()]})
tb=R['tb'].reset_index(); sg=R['sg'].reset_index()
ty=box.groupby('type').agg(so_hop=('Mac','size'),gio_xem_TB=('total_h','mean'),ngay_hoat_dong_TB=('active_days','mean')).reset_index()
box_out=box.drop(columns=['MAC'],errors='ignore')
with pd.ExcelWriter('out/FPT_Play_Analysis_Summary.xlsx',engine='openpyxl') as w:
    for n,d in [('KPI',k),('Theo_gio',hr),('Kenh_TV',ch_t),('Phim_VOD_top100',vt),('VOD_theo_nuoc',vc),('Tinh_nang',ad),('Thoi_gian_gan_bo',tb),('Phan_khuc_hop',sg),('Kieu_khach',ty),('Bang_theo_hop',box_out)]:
        d.round(2).to_excel(w,sheet_name=n,index=False)
    from openpyxl.styles import Font,PatternFill
    for ws in w.book.worksheets:
        for c in ws[1]: c.font=Font(name='Arial',bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='1F6FEB')
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=max(12,min(40,max(len(str(c.value or '')) for c in col[:60])+2))
print('ok')
