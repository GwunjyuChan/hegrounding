import json,os,re,collections
H=os.path.expanduser('~/mnt/hegrounding/')
B=H+'.deploy/scan_20261119/'
FX=B+'full_texts_fixed/'; F1=B+'full_texts/'
recs=[json.loads(l) for l in open(H+'benchmark/annotations/dataset_v2_20261116/annotations.jsonl')]
texts=json.load(open(B+'texts.json')); res={tuple(x['ids']):x for x in json.load(open(B+'result.json'))}
log=json.load(open(FX+'fixes_log.json'))
m1=json.load(open(F1+'mapping_batch1.json'))
explicit={}
for fn,v in m1.items():
    if fn.startswith('_'): continue
    for i in v['items']: explicit[i]=(F1+fn,v)
group={}
for x in texts:
    for i in x['ids']: group[i]=tuple(x['ids'])
GAZ=['NC2-SP-024','NC2-SP-025','NC2-SP-026','NC2-SP-027','NC2-SP-029']
PENDING={'MF0101':'Chambray 1823 t.II: current text has [...] elisions; full contiguous French passage needs page scans (OCR unusable)',
 'MF0103':'same as MF0101','MF0104':'same as MF0101'}
for i in ['NC2-SP-013','NC2-SP-014','NC2-SP-015','NC2-SP-016','NC2-SP-017','NC2-SP-018','NC2-SP-019','NC2-SP-020','NC2-SP-021']:
    PENDING[i]='Holcroft 1780: OCR unusable, needs page images'
rejected=set('NC-WW1-057 NC2-DS-003 NC2-PH-006 NC2-PH-029 NC2-PH-030 NC2-PH-031 NC2-PH-032 NC2-PH-034 NC2-PH-036 NC2-PH-044 NC2-SP-001 NC2-SP-036'.split())
out=[]; stats=collections.Counter(); gaps=[]
for r in recs:
    i=r['event_id']; s=r['source_record']; lang=s.get('source_language','en')
    g=group.get(i,(i,))
    f=None; note=None
    if i in explicit: f,v=explicit[i]; note=v
    elif i in GAZ: f=FX+'gazette_morning_18th.txt'; note={'note':'whole Gazette passage shared by SP-024/025/026/027/029; ends with a colon before the order-of-march tables'}
    else:
        for j in (i,)+g:
            if os.path.exists(FX+j+'.txt'): f=FX+j+'.txt'; note=log.get(j); break
    if f:
        t=open(f).read().strip(); origin='full_paragraph_checked'
    elif i in PENDING:
        t=(s.get('source_text') if lang!='en' else s.get('event_text')) or s.get('event_text'); origin='PENDING'; note={'note':PENDING[i]}
    else:
        t=(s.get('source_text') if lang!='en' else s.get('event_text')) or s.get('event_text'); origin='unchanged'
        rr=res.get(g)
        if rr and (rr.get('lead') not in (0,None) or rr.get('tail') not in (0,None)) : gaps.append((i,rr.get('lead'),rr.get('tail')))
        if rr and rr.get('lead') is None: gaps.append((i,'unmatched',''))
        note={'note':'scan found text already starts and ends at paragraph boundaries' if rr and rr.get('lead')==0 and rr.get('tail')==0 else 'not re-checked in this pass'}
    stats[origin]+=1
    out.append({'event_id':i,'model_input_text':t,'model_input_language':lang,'review_text_unchanged':True,
                'origin':origin,'file':os.path.relpath(f,H) if f else None,'shared_with':[j for j in g if j!=i],
                'rejected_in_review':i in rejected,'notes':note})
print(stats); print('gaps',gaps)
D=H+'benchmark/model_inputs/'; os.makedirs(D,exist_ok=True)
with open(D+'model_inputs_v2_20261119.jsonl','w') as fh:
    for o in out: fh.write(json.dumps(o,ensure_ascii=False)+'\n')
print('written',len(out))
