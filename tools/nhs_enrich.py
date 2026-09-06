#!/usr/bin/env python3
"""
nhs_enrich.py — regenerate the NHS enrichment of system-data.json from NHS ODS + Code-Point Open.

Idempotent: strips its own previous output, then re-applies. Re-run it after re-downloading the
ODS files to refresh codes, the community-pharmacy layer, and trust/ICB structure — and to surface
drift (newly closed / unmatched practices are flagged status=verify for a human to review, never
silently dropped).

Owns, in system-data.json:
  - ods / ods_name / postcode / ods_ics fields on primary-care + trust/ICB nodes
  - all PHARM:* (pharmacy) and PHARMHQ:* (owner) nodes and their edges
  - edges labelled 'operated by', 'commissions pharmaceutical services', 'ICB partner'
  - the curated practice adds/removes/overrides in CURATION below
Everything else in the file is hand-authored and left untouched.

Data sources (override with env vars; defaults are Peter's Mac paths):
  DATA_ROOT   = .../RCVDA - Documents/Data
  GP files    = $DATA_ROOT/NHS/Organisation Data Service (ODS) - GP and GP Practice Related Data
  Other NHS   = $DATA_ROOT/NHS/Organisation Data Service (ODS) - Other NHS organisations
  Code-Point  = $DATA_ROOT/Office for National Statistics (ONS)/Post Code Data/codepo_gb/Data/CSV

Usage:
  python3 tools/nhs_enrich.py           # write in place, print summary (review with: git diff)
  python3 tools/nhs_enrich.py --dry-run # print summary only, write nothing
"""
import csv, json, re, os, sys, difflib
from collections import defaultdict, Counter

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATAF  = os.path.join(ROOT, "data", "system-data.json")
DATA_ROOT = os.environ.get("DATA_ROOT",
    "/Users/peterneal/Library/CloudStorage/OneDrive-SharedLibraries-RCVDA/RCVDA - Documents/Data")
GP     = os.environ.get("NHS_GP_DIR",    os.path.join(DATA_ROOT, "NHS", "Organisation Data Service (ODS) - GP and GP Practice Related Data"))
OTHER  = os.environ.get("NHS_OTHER_DIR", os.path.join(DATA_ROOT, "NHS", "Organisation Data Service (ODS) - Other NHS organisations"))
PCD    = os.environ.get("CODEPOINT_DIR", os.path.join(DATA_ROOT, "Office for National Statistics (ONS)", "Post Code Data", "codepo_gb", "Data", "CSV"))
DRYRUN = "--dry-run" in sys.argv

GPURL  = "https://digital.nhs.uk/services/organisation-data-service/data-search-and-export/csv-downloads/gp-and-gp-practice-related-data"
ODSURL = "https://digital.nhs.uk/services/organisation-data-service/data-search-and-export/csv-downloads/other-nhs-organisations"
ICB    = "NHS North East & North Cumbria ICB"
CCG16C = "16C"   # former NHS Tees Valley CCG / TV sub-ICB location — the Tees Valley filter

# ---- CURATION: the human decisions a fuzzy match can't make. Edit here, not the JSON. ----
PRACTICE_OVERRIDES = {          # map label -> ODS practice code (evidence in the session notes)
    "Drs Koh & Trory": "A81060",           # West Quay MP — GP register lists Koh + Trory there
    "The Greenhouse Surgery": "A81052",     # ODS 'The Green House Surgery'
    "Seaton Surgery": "A81612",             # ODS 'The Patel Practice', Station Lane, Seaton Carew
    "St Georges Medical Practice": "A83070",# ODS 'Middleton & Dinsdale', at Middleton St George
}
REMOVE_PRACTICE_LABELS = ["Wynyard Road Practice"]  # duplicate of McKenzie Group (A81070)
ADD_PRACTICES = [               # active ODS practices missing from the hand-authored map
    {"label": "McKenzie House Surgery", "ods": "A81044", "pcn": "Hartlepool Health PCN",
     "area": "E06000001", "area_label": "Hartlepool", "ceremonial": "county-durham"},
]
TRUST_ODS = {                   # map node id -> ODS 'etr' name to look up its code
    "South Tees Hospitals NHS Foundation Trust": "SOUTH TEES HOSPITALS NHS FOUNDATION TRUST",
    "North Tees and Hartlepool NHS Foundation Trust": "NORTH TEES AND HARTLEPOOL NHS FOUNDATION TRUST",
    "Tees Esk & Wear Valleys NHS FT": "TEES, ESK AND WEAR VALLEYS NHS FOUNDATION TRUST",
    "North East Ambulance Service NHS FT": "NORTH EAST AMBULANCE SERVICE NHS FOUNDATION TRUST",
    "County Durham and Darlington NHS Foundation Trust": "COUNTY DURHAM AND DARLINGTON NHS FOUNDATION TRUST",
}
ICB_ODS = "QHM"; ICB_ICS = "E54000050"
ICB_PARTNERS = [               # in-map NENC ICB partners lacking an ICB link (councils + CDDFT)
    "Middlesbrough Council", "Redcar & Cleveland Borough Council", "Stockton-on-Tees Borough Council",
    "Darlington Borough Council", "Hartlepool Borough Council",
    "County Durham and Darlington NHS Foundation Trust",
]
TVLAD = {'E06000001':('Hartlepool','county-durham','AREA:Hartlepool'),
         'E06000002':('Middlesbrough','north-yorkshire','AREA:Middlesbrough'),
         'E06000003':('Redcar and Cleveland','north-yorkshire','AREA:Redcar and Cleveland'),
         'E06000004':('Stockton-on-Tees','county-durham','AREA:Stockton-on-Tees'),
         'E06000005':('Darlington','county-durham','AREA:Darlington')}
CLEV = {'E06000001','E06000002','E06000003','E06000004'}

def rows(p): return list(csv.reader(open(p, encoding='latin-1')))
def npc(s): return (s or '').replace(' ', '').upper()
def smartcase(s):
    s = s.title()
    for a,b in [('Uk','UK'),('Nhs','NHS'),("'S","'s")]: s = s.replace(a,b)
    return re.sub(r'\bPlc\b','PLC',s)

# ---------- load ----------
for pth,lbl in [(DATAF,'system-data.json'),(GP,'GP ODS dir'),(OTHER,'Other-NHS dir'),(PCD,'Code-Point dir')]:
    if not os.path.exists(pth): sys.exit("ERROR: %s not found: %s" % (lbl, pth))
d = json.load(open(DATAF))
before = json.dumps(d, ensure_ascii=False, sort_keys=True)

# ---------- 1. strip prior output (idempotency) ----------
OWNED_EDGE_LABELS = {'operated by', 'commissions pharmaceutical services', 'ICB partner'}
OWNED_EDGE_ID = {(e['data']['source'],e['data']['target'],e['data'].get('label')):e['data'].get('id')
                 for e in d['edges'] if e['data'].get('label') in {'operated by','commissions pharmaceutical services','ICB partner'}}
d['nodes'] = [n for n in d['nodes'] if not n['data']['id'].startswith(('PHARM:', 'PHARMHQ:'))]
for n in d['nodes']:
    for k in ('ods','ods_name','postcode','ods_ics'):
        n['data'].pop(k, None)
gone = {n['data']['id'] for n in d['nodes']}  # surviving ids
d['edges'] = [e for e in d['edges']
              if e['data'].get('label') not in OWNED_EDGE_LABELS
              and e['data']['source'] in gone and e['data']['target'] in gone]

byid = {n['data']['id']: n['data'] for n in d['nodes']}

# ---------- 2. postcode -> LAD ----------
pc2lad = {}
for a in ('ts.csv','dl.csv'):
    fp = os.path.join(PCD,a)
    if os.path.exists(fp):
        for r in rows(fp):
            if len(r)>8 and r[8] in TVLAD: pc2lad[npc(r[0])] = r[8]

# ---------- 3. PCN codes ----------
epcn = [r for r in rows(os.path.join(GP,'epcn.csv')) if len(r)>3 and r[2]==CCG16C]
def npcn(s):
    s = re.sub(r'[^A-Z0-9 ]',' ',(s or '').upper())
    s = re.sub(r'\bPCN\b|\bLTD\b|\bLIMITED\b|\bAND\b','',s); return re.sub(r'\s+',' ',s).strip()
odspcn = {npcn(r[1]):(r[0],r[1]) for r in epcn}
pcn_label2u = {}
for n in d['nodes']:
    x = n['data']
    if x.get('type')=='NHS body' and x.get('group')=='Primary care' and x.get('subtype')!='practice':
        hit = odspcn.get(npcn(x['label']))
        if not hit:
            for k,v in odspcn.items():
                if npcn(x['label']) and (npcn(x['label']) in k or k in npcn(x['label'])): hit=v; break
        if hit:
            x['ods'] = hit[0]; pcn_label2u[x['label']] = hit[0]
            if hit[1].upper()!=x['label'].upper(): x['ods_name'] = hit[1]

# ---------- 4. practices ----------
epraccur = {r[0]:r for r in rows(os.path.join(GP,'epraccur.csv')) if len(r)>14}
members = [r for r in rows(os.path.join(GP,'epcncorepartnerdetails.csv'))
           if len(r)>6 and r[2]==CCG16C and (len(r)<10 or r[9]=='')]
by_u = defaultdict(list)
for r in members: by_u[r[4]].append((r[0], r[1]))
STOP = {'THE','SURGERY','SURGERIES','PRACTICE','MEDICAL','CENTRE','CENTER','HEALTH','DR','DRS','AND','PMS'}
def toks(s):
    s = re.sub(r'\[.*?\]',' ',(s or '').upper()); s = re.sub(r'[^A-Z0-9 ]',' ',s)
    return set(w for w in s.split() if len(w)>2 and w not in STOP)
def lnorm(s):
    s = re.sub(r'\[.*?\]',' ',(s or '').upper()); s = re.sub(r'[^A-Z0-9 ]',' ',s); return re.sub(r'\s+',' ',s).strip()
def score(a,b):
    ta,tb = toks(a),toks(b); jac = len(ta&tb)/max(1,len(ta|tb))
    return 0.65*jac + 0.35*difflib.SequenceMatcher(None,lnorm(a),lnorm(b)).ratio()

# remove curated duplicate/removed practices
rm_ids = [n['data']['id'] for n in d['nodes']
          if n['data'].get('subtype')=='practice' and n['data']['label'] in REMOVE_PRACTICE_LABELS]
d['nodes'] = [n for n in d['nodes'] if n['data']['id'] not in rm_ids]
d['edges'] = [e for e in d['edges'] if e['data']['source'] not in rm_ids and e['data']['target'] not in rm_ids]
byid = {n['data']['id']: n['data'] for n in d['nodes']}

flags = []
def closed_date(code):
    r = epraccur.get(code)
    return r[11] if (r and len(r)>12 and r[12]!='ACTIVE' and r[11]) else None

mapprac = [n['data'] for n in d['nodes'] if n['data'].get('subtype')=='practice']
used = set()
# overrides first
for n in mapprac:
    if n['label'] in PRACTICE_OVERRIDES:
        code = PRACTICE_OVERRIDES[n['label']]; used.add(code); r = epraccur.get(code)
        n['ods'] = code; n['postcode'] = r[9] if r else ''
        if r and r[1].upper()!=n['label'].upper(): n['ods_name'] = r[1]
        cd = closed_date(code)
        if cd: n['status']='verify'; flags.append((n['label'],'OVERRIDE code now CLOSED '+cd))
# within-PCN assignment for the rest
auto = [n for n in mapprac if n['label'] not in PRACTICE_OVERRIDES]
bypcn = defaultdict(list)
for n in auto: bypcn[pcn_label2u.get(n.get('org',''),'?')].append(n)
for u, ns in bypcn.items():
    cand = [c for c in by_u.get(u,[]) if c[0] not in used]
    pairs = sorted(((score(n['label'],nm), n, c, nm) for n in ns for c,nm in cand), key=lambda x:-x[0])
    done = set()
    for sc,n,c,nm in pairs:
        if id(n) in done or c in used or sc<0.45: continue
        used.add(c); done.add(id(n)); r = epraccur[c]
        n['ods'] = c; n['postcode'] = r[9]
        if r[1].upper()!=n['label'].upper(): n['ods_name'] = r[1]
        cd = closed_date(c)
        if cd: n['status']='verify'; flags.append((n['label'], 'matched %s but ODS shows CLOSED %s'%(c,cd)))
    for n in ns:
        if id(n) not in done:
            n['status']='verify'; flags.append((n['label'], 'no current ODS match — review'))

# add curated missing practices (idempotent upsert)
for a in ADD_PRACTICES:
    pid = 'PRAC:'+a['ods']; r = epraccur.get(a['ods'])
    nd = {'id':pid,'label':a['label'],'type':'NHS body','tier':'local','geography':a['area_label'],
          'status':'confirmed','org':a['pcn'],'subtype':'practice','person':'','portfolio':'',
          'description':'GP practice · '+a['pcn'],'source':GPURL,'parent':a.get('parent','AREA:'+a['area_label']),
          'group':'Primary care','area':a['area'],'area_label':a['area_label'],'ceremonial':a['ceremonial'],
          'ods':a['ods'],'postcode':(r[9] if r else '')}
    existing = byid.get(pid)
    if existing: existing.update(nd)
    else:
        d['nodes'].append({'data':nd})
        d['edges'].append({'data':{'source':pid,'target':a['pcn'],'label':'member practice','kind':'delivery','weight':1,'id':None}})
byid = {n['data']['id']: n['data'] for n in d['nodes']}

# ---------- 5. pharmacy + owner layer ----------
disp = [r for r in rows(os.path.join(GP,'edispensary.csv')) if len(r)>14 and r[12]=='ACTIVE']
hqname = {r[0]:r[1] for r in rows(os.path.join(GP,'epharmacyhq.csv')) if len(r)>1}
tvph = [(r, pc2lad[npc(r[9])]) for r in disp if npc(r[9]) in pc2lad]
owner_lads = defaultdict(set); owner_name = {}
for r,lad in tvph:
    hq = r[14] if r[14] else 'IND:'+r[0]
    owner_lads[hq].add(lad); owner_name[hq] = hqname.get(r[14]) if r[14] else smartcase(r[1])
owner_id = {}; new_nodes = []; new_edges = []
for hq,lads in owner_lads.items():
    oid = 'PHARMHQ:'+hq; owner_id[hq] = oid
    if len(lads)==1: lad=next(iter(lads)); lbl,cer,_=TVLAD[lad]; area,al,ti,cv = lad,lbl,'local',cer
    elif lads<=CLEV: area,al,ti,cv = 'cleveland','Cleveland','sub-regional',''
    else: area,al,ti,cv = 'tees-valley','Tees Valley','sub-regional',''
    new_nodes.append({'data':{'id':oid,'label':owner_name[hq],'type':'NHS body','tier':ti,'geography':al,
        'status':'confirmed','org':'','subtype':'pharmacy owner','person':'','portfolio':'',
        'description':'Community pharmacy owner/operator','source':ODSURL if False else GPURL,'group':'Primary care',
        'area':area,'area_label':al,'ceremonial':cv,'ods':(hq if not hq.startswith('IND:') else '')}})
    new_edges.append({'data':{'source':ICB,'target':oid,'label':'commissions pharmaceutical services','kind':'commissioning','weight':2,'id':OWNED_EDGE_ID.get((ICB,oid,'commissions pharmaceutical services'))}})
for r,lad in tvph:
    code=r[0]; lbl,cer,par=TVLAD[lad]; hq=r[14] if r[14] else 'IND:'+code; pid='PHARM:'+code
    if pid in byid: continue
    new_nodes.append({'data':{'id':pid,'label':smartcase(r[1]),'type':'NHS body','tier':'local','geography':lbl,
        'status':'confirmed','org':owner_name[hq],'subtype':'pharmacy','person':'','portfolio':'',
        'description':'Community pharmacy · %s · %s'%(owner_name[hq],r[9]),'source':GPURL,'parent':par,
        'group':'Primary care','area':lad,'area_label':lbl,'ceremonial':cer,'ods':code,'postcode':r[9]}})
    new_edges.append({'data':{'source':pid,'target':owner_id[hq],'label':'operated by','kind':'governance','weight':1,'id':OWNED_EDGE_ID.get((pid,owner_id[hq],'operated by'))}})
d['nodes'].extend(new_nodes); d['edges'].extend(new_edges)
byid = {n['data']['id']: n['data'] for n in d['nodes']}

# ---------- 6. trusts + ICB ----------
etr = rows(os.path.join(OTHER,'etr.csv'))
trust_code = {}
for nid,name in TRUST_ODS.items():
    for r in etr:
        if len(r)>1 and r[1].upper()==name: trust_code[nid]=r[0]; break
for nid,code in trust_code.items():
    if nid in byid: byid[nid]['ods']=code
if ICB in byid:
    byid[ICB]['ods']=ICB_ODS; byid[ICB]['ods_ics']=ICB_ICS
uht = byid.get('University Hospitals Tees (UHT)')
if uht:
    note='Group brand for South Tees Hospitals (RTR) + North Tees & Hartlepool (RVW) — not a separate ODS legal entity.'
    if note not in uht.get('description',''):
        uht['description']=((uht.get('description','')+' · '+note).strip(' ·'))
existing_icb = set(frozenset((e['data']['source'],e['data']['target'])) for e in d['edges']
                   if ICB in (e['data']['source'],e['data']['target']))
for pr in ICB_PARTNERS:
    if pr in byid and frozenset((pr,ICB)) not in existing_icb:
        d['edges'].append({'data':{'source':pr,'target':ICB,'label':'ICB partner','kind':'membership','weight':2,'id':OWNED_EDGE_ID.get((pr,ICB,'ICB partner'))}})

# ---------- renumber any new edge ids, provenance, validate ----------
used_e = set(e['data']['id'] for e in d['edges'] if e['data'].get('id'))
mx = max([int(re.sub(r'\D','',i)) for i in used_e if re.sub(r'\D','',i)] + [0])
for e in d['edges']:
    if not e['data'].get('id'):
        mx += 1; e['data']['id'] = 'e%d'%mx
d.setdefault('sources',{})
d['sources']['NHS primary care — ODS codes & pharmacies']=GPURL
d['sources']['NHS trusts & ICB — ODS organisation codes']=ODSURL
ids = [n['data']['id'] for n in d['nodes']]
assert len(ids)==len(set(ids)), "duplicate node ids"
ns = set(ids)
assert not [e for e in d['edges'] if e['data']['source'] not in ns or e['data']['target'] not in ns], "dangling edge"
pods = [n['data']['ods'] for n in d['nodes'] if n['data'].get('subtype')=='practice' and n['data'].get('ods')]
assert len(pods)==len(set(pods)), "duplicate practice ODS: %s"%[c for c in pods if pods.count(c)>1]

# ---------- report ----------
prac = [n['data'] for n in d['nodes'] if n['data'].get('subtype')=='practice']
ph   = [n for n in d['nodes'] if n['data'].get('subtype')=='pharmacy']
own  = [n for n in d['nodes'] if n['data'].get('subtype')=='pharmacy owner']
print("PCNs coded: %d | practices: %d (coded %d, verify %d)" % (
    len(pcn_label2u), len(prac),
    sum(1 for x in prac if x.get('ods') and x.get('status')!='verify'),
    sum(1 for x in prac if x.get('status')=='verify')))
print("pharmacies: %d | owners: %d | trust codes: %d | totals: nodes %d edges %d" % (
    len(ph), len(own), len(trust_code), len(d['nodes']), len(d['edges'])))
if flags:
    print("\n*** REVIEW — practices needing a human decision (%d): ***" % len(flags))
    for lbl,why in flags: print("   -", lbl, "|", why)
else:
    print("no practices flagged for review.")

after = json.dumps(d, ensure_ascii=False, sort_keys=True)
if before==after:
    print("\nNo change — system-data.json already matches the source data.")
elif DRYRUN:
    print("\n[--dry-run] changes computed but NOT written.")
else:
    json.dump(d, open(DATAF,'w'), ensure_ascii=False, indent=1)
    print("\nWrote data/system-data.json. Review with: git diff data/system-data.json")
