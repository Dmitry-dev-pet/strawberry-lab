import json, csv
from pathlib import Path
from collections import Counter

root=Path('/mnt/data/fruit-morphometry')
out=root/'measurements-v1.json'

sources = {
 'JAMES1974': {
   'title':'David John James (1974), A Cytochemical and Biochemical Study of Acid Hydrolases in Developing Plant Cells',
   'url':'https://gala.gre.ac.uk/id/eprint/9233/1/David_John_James_1974.pdf',
   'type':'PhD thesis, primary measurements',
   'taxon':'Fragaria × ananassa',
   'access':'full extracted PDF text; PDF screenshot not available (cache miss)',
   'tables':['IV.1 (p.104)','IV.3 (p.107)'],
   'scope':'Cultivar Cambridge Vigour; IV.1 growth stages 1969, IV.3 microscopy measurements 1972; 10 cell observations per developmental stage in IV.3',
   'access_caveat':'Use printed page numbers. IV.1 selection sizes A/B are nominal criteria, NOT means. IV.3 D/E missing.'
 },
 'ARIZA2011':{
   'title':'Ariza et al. (2011), Fruit misshapen in strawberry cultivars is related to achenes functionality, Annals of Applied Biology 158, 130–138',
   'url':'https://www.researchgate.net/publication/229735697_Fruit_misshapen_in_strawberry_cultivars_Fragariaananassa_is_related_to_achenes_functionality',
   'doi':'10.1111/j.1744-7348.2010.00451.x',
   'type':'Research article; full text of original article indexed via ResearchGate',
   'taxon':'Fragaria × ananassa',
   'access':'original published table in accessible article text (ResearchGate mirror), not publisher original PDF',
   'tables':['Table 2 (p.134)'],
   'scope':'Field-grown Camarosa, Medina, Ventana; well-formed (WF) vs misshapen (MF); means ±SE of n=3 plot averages; 50 fruits/plot for size, 30 fruits/plot for achene size/class counts',
   'access_caveat':'Big achenes defined >0.6 mm; small <0.4 mm; intermediate sizes not included in big/small counts. Table 2 number of total achenes need not equal sum of these classes.'
 },
 'CURRIE1997':{
   'title':'Michael Brian Currie (1997), Source-Sink Relations in Kiwifruit, PhD thesis, Massey University',
   'url':'https://mro.massey.ac.nz/server/api/core/bitstreams/c524d403-4e01-4d2e-8c09-e0d4057b09b3/content',
   'type':'PhD thesis, primary histology',
   'taxon':'Actinidia deliciosa',
   'access':'full extracted PDF text; PDF screenshot not available (cache miss)',
   'tables':['3.4 (p.3-20)','3.5 (p.3-21/22)','3.1 (p.3-6)'],
   'scope':'Chapter 3 girdling experiment on green-fleshed A. deliciosa (cultivar not stated for this specific table in the extracted methods; Hayward is common in the study but not guaranteed for these rows), harvested 150 days after full bloom for 3.4 and 3.5, leaf:fruit ratios 1 vs 4, girdling at day 7/28/56. Marginal means (PMM) due to missing data.',
   'access_caveat':'Table 3.4 diameter along Dmax/Dmin transects, not isotropic cell diameter. Table 3.5 counts are per straight radial transect, not total fruit counts. Thesis copyright: private study only, reproduce factual numerical observations but not original images/chapters.'
 },
 'JEON2024':{
   'title':'Jeon, Oh & Song (2024), Response of Fruit Growth and Quality to the Spray of Plant Growth Regulator in Yellow-fleshed Kiwifruits, Horticultural Science & Technology 42, 234–246',
   'url':'https://www.hst-j.org/articles/xml/G2NO/',
   'doi':'10.7235/HORT.20240020',
   'type':'Primary research article; publisher full HTML',
   'taxon':'Actinidia chinensis var. chinensis',
   'access':'full publisher HTML tables and methods',
   'tables':['3 (fruit tissue width, mm)','4 (sample cell counts)','5 (cell size, µm)'],
   'scope':'Yellow-fleshed Sweet Gold and Jecy Gold grown in Jeju; Control/one/two/three sprays of Benefits PZ starting after bloom; cell samples ~1.2×1.2 mm, 10 samples each treatment, per authors methods; tissue widths n=3, cells n=10, mean ±SE.',
   'access_caveat':'Table 3 widths are total measured radial components, not whole-fruit diameter; totals 21–25 mm for one side. Table 4 cell counts in samples, not number of all cells in fruit.'
 },
}
rows=[]
def add(source,taxon,cultivar,organ,tissue,metric,value,unit,*,se=None,n=None,stat='mean',stage='',treatment='',axis='',note='',locator='',source_label='',importance='experiment',uncertainty_kind=None):
  assert source in sources and value is not None
  rows.append({'id':f'R{len(rows)+1:04d}','source_id':source,'source_locator':locator or sources[source]['tables'][0], 'taxon':taxon, 'cultivar':cultivar, 'organ':organ, 'tissue':tissue,'metric':metric,'axis':axis,'stage':stage,'treatment':treatment,'value':value,'unit':unit,'uncertainty_value':se,'uncertainty_kind':uncertainty_kind or ('SEM' if se is not None else ''),'n':n,'statistic':stat,'evidence':'PRIMARY_TABLE','usage':'OBSERVATION_ONLY','note':note})

S='Fragaria × ananassa'
for stage,l,w,le,we in [('A',41.1,30.7,1.7,1.4),('B',59.9,38.2,5.3,1.7),('C',109.5,73.6,6.9,3.6)]:
 for metric,value,sem in [('cell_maximum_length',l,le),('cell_maximum_breadth',w,we)]:
  add('JAMES1974',S,'Cambridge Vigour','receptacle','cortex',metric,value,'µm',se=sem,n=10,stage=stage,treatment='none',locator='Table IV.3, printed p.107, crop 1972',note='Zeiss microscope eyepiece graticule; cortex at maximum fruit girth; A/B/C only; 10 cell observations')
for stage,height,width in [('A',2.5,1.7),('B',5.0,3.2)]:
 for metric,value in [('receptacle_selection_height',height),('receptacle_selection_width',width)]:
  add('JAMES1974',S,'Cambridge Vigour','receptacle','whole',metric,value,'mm',stat='selection_criterion',stage=stage,treatment='none',locator='Table IV.1, printed p.104',note='Nominal selection-size criterion, not sample mean; height to basal vascular bundle')
for stage,mean,se,n in [('C',5.70,0.37,94),('D',8.37,0.26,72),('E',10.84,0.23,83)]:
 add('JAMES1974',S,'Cambridge Vigour','receptacle','whole','fruit_fresh_weight',mean,'g',se=se,n=n,stage=stage,treatment='none',locator='Table IV.1, printed p.104, crop 1969')

ariza = [
 ('Camarosa','well_formed',22.07,.94,4.80,.07,3.25,.03,325.6,17.8,253.4,17.9,56.6,3.7),
 ('Camarosa','misshapen',14.89,.87,3.80,.11,2.83,.06,159.3,8.8,89.6,4.4,62.1,4.1),
 ('Medina','well_formed',28.43,.45,4.99,.05,3.55,.02,335.7,10.3,285.92,6.7,33.8,3.4),
 ('Medina','misshapen',25.48,.71,4.87,.10,3.30,.03,221.8,7.8,118.3,7.2,92.9,3.1),
 ('Ventana','well_formed',20.61,.11,4.25,.02,3.28,.01,265.3,14.2,229.6,10.3,23.0,3.4),
 ('Ventana','misshapen',11.12,.12,3.08,.02,2.40,.01,156.6,9.7,67.2,3.3,81.9,7.3),
]
for (cult,shape,weight,wse,length,lse,width,widse,total,tse,big,bse,small,sse) in ariza:
 for metric,val,se,unit,organ,tn in [
 ('fruit_fresh_weight',weight,wse,'g','receptacle','whole'),('fruit_length',length,lse,'cm','receptacle','whole'),
 ('fruit_width',width,widse,'cm','receptacle','whole'),('achene_total_per_fruit',total,tse,'count','achenes','surface'),
 ('achene_big_over_0.6mm_per_fruit',big,bse,'count','achenes','surface'),('achene_small_under_0.4mm_per_fruit',small,sse,'count','achenes','surface')]:
  add('ARIZA2011',S,cult,organ,tn,metric,val,unit,se=se,n=3,stage='field_harvest',treatment='fruit_shape='+shape,locator='Table 2, published p.134',note='Mean±SE across 3 plot averages; fruit sample counts differ by metric. Counts of size classes exclude intermediates.')

K='Actinidia deliciosa'
# Caution cultivar intentionally unspecified: thesis Chapter3 discusses Hayward elsewhere but method does not name cultivar for these rows.
c34=[(7,'low',100,55,217,89,115),(28,'low',92,63,175,71,103),(56,'low',107,62,232,85,122),(7,'high',121,69,233,111,137),(28,'high',117,69,219,96,130),(56,'high',109,68,251,96,134)]
for d,leaf,coremax,coremin,inner,outer,tot in c34:
 for tissue,metric,axis,value in [
 ('core','cell_transect_diameter','Dmax',coremax),('core','cell_transect_diameter','Dmin',coremin),
 ('inner_pericarp','cell_transect_diameter','Dmin',inner),('outer_pericarp','cell_transect_diameter','Dmin',outer),
 ('half_fruit_all_regions','cell_transect_diameter','Dmin',tot)]:
  add('CURRIE1997',K,'cultivar_unverified_ch3','fruit',tissue,metric,value,'µm',stage='150_DAFB',treatment=f'girdled_day={d};leaf_fruit_ratio={1 if leaf=="low" else 4}',axis=axis,stat='population_marginal_mean',locator='Table 3.4, chapter 3 printed p.3-20',note='Girdled treatments; Dmax/Dmin transect average. Averages influenced by experimental treatments, not untreated cultivar defaults.')
c35=[(7,'low',73,231,8.7,62,43.7),(28,'low',48,191,7.3,56,45.8),(56,'low',63,197,8.3,68,45.0),(7,'high',144,290,8.3,82,47.5),(28,'high',129,255,8.0,78,41.0),(56,'high',98,247,9.3,79,41.0)]
for d,leaf,weight,large_d,large_n,small_d,small_n in c35:
 for tissue,metric,value,unit in [
  ('whole','fruit_fresh_weight',weight,'g'),('outer_pericarp_large','cell_transect_diameter',large_d,'µm'),('outer_pericarp_large','cell_number_on_radial_transect',large_n,'count'),
  ('outer_pericarp_small','cell_transect_diameter',small_d,'µm'),('outer_pericarp_small','cell_number_on_radial_transect',small_n,'count')]:
  add('CURRIE1997',K,'cultivar_unverified_ch3','fruit',tissue,metric,value,unit,stage='150_DAFB',treatment=f'girdled_day={d};leaf_fruit_ratio={1 if leaf=="low" else 4}',axis='Dmin',stat='population_marginal_mean',locator='Table 3.5, chapter 3 printed p.3-21/22',note='Counts along one outer-pericarp transect, not whole-fruit cell numbers. PMM treatment values.')

K2='Actinidia chinensis var. chinensis'
# Jeon 2024: source labels Tables 3,4,5 full published HTML. Rows with means ± standard error.
# Table 3: core, inner and outer pericarp one-sided tissue widths, total.
j3={
 'Sweet Gold':[(0,(3.6,1.2),(10.4,1.2),(7.3,1.1),(21.3,.2)),(1,(3.8,1.1),(10.3,1.8),(8.1,1.3),(22.2,.3)),(2,(4.2,.9),(10.5,1.5),(8.5,1.4),(23.2,.2)),(3,(4.5,.9),(10.2,1.1),(9.3,.9),(24.0,.3))],
 'Jecy Gold':[(0,(3.0,.8),(8.6,1.2),(9.1,.9),(20.7,.1)),(1,(3.2,1.2),(8.6,1.3),(11.1,1.1),(22.9,.1)),(2,(3.3,.6),(9.4,1.5),(11.5,.6),(24.2,.1)),(3,(3.6,.9),(9.5,1.1),(11.9,1.1),(25.0,.1))]
}
for cultivar,entries in j3.items():
 for spr,core,inner,outer,total in entries:
  for tissue,(val,se) in zip(['core','inner_pericarp','outer_pericarp','half_radial_total'],[core,inner,outer,total]):
   add('JEON2024',K2,cultivar,'fruit',tissue,'radial_tissue_width',val,'mm',se=se,n=3,stage='harvest_180_DAA',treatment=f'BenefitsPZ_sprays={spr}',axis='radial_from_center',locator='Table 3, 2024, p.??? publisher HTML',note='Widths at central fruit section, sum of core+inner+outer = half radial total; mean ± SE, n=3.')

# Table 4: counts in sampled regions, n=10 samples per treatment; NOT total fruit count
j4={
 'Sweet Gold':[(0,(76.1,.8),(108.7,.9),(142.1,3.9),(24.2,1.6)),(1,(78.0,.8),(109.0,1.5),(148.9,3.1),(23.6,1.4)),(2,(86.7,.8),(110.2,1.7),(159.4,3.6),(27.7,1.1)),(3,(90.1,.6),(109.6,1.0),(175.1,3.9),(27.8,1.2))],
 'Jecy Gold':[(0,(64.0,.6),(100.7,1.0),(140.3,1.3),(33.5,2.0)),(1,(67.4,.6),(101.2,.7),(152.6,2.8),(34.2,1.9)),(2,(69.6,.6),(111.5,.6),(163.5,2.7),(34.6,1.5)),(3,(71.7,.5),(113.3,.8),(170.1,2.6),(35.8,None))]
}
for cultivar,entries in j4.items():
 for spr,*vals in entries:
  for tissue,(val,se) in zip(['core','inner_pericarp','outer_pericarp_small','outer_pericarp_large'],vals):
   add('JEON2024',K2,cultivar,'fruit',tissue,'cell_number_in_sample',val,'count',se=se,n=10,stage='harvest_180_DAA',treatment=f'BenefitsPZ_sprays={spr}',locator='Table 4, publisher HTML, 2024',note='Sample counts (10 fixed tissue samples 1.2×1.2 mm), not total cells per fruit. Published Table4 Jecy Gold thrice large-cell SEM appears as .1.5 (typographic issue); left unset, do NOT infer its value.' if (cultivar=='Jecy Gold' and spr==3 and tissue=='outer_pericarp_large') else 'Cell counts for sampled tissue (n=10, samples 1.2×1.2 mm), not whole fruit totals.',uncertainty_kind='SEM_unreadable_typo_in_source' if cultivar=='Jecy Gold' and spr==3 and tissue=='outer_pericarp_large' else None)

# Table 5: mean cell size µm, sample n=10
j5={
 'Sweet Gold':[(0,(47.3,.2),(95.9,.8),(51.4,1.4),(164.6,4.7)),(1,(48.7,.3),(94.9,1.4),(54.5,1.1),(182.4,4.3)),(2,(48.4,.2),(95.1,1.7),(53.9,1.3),(167.2,4.0)),(3,(49.9,.2),(93.9,.9),(53.5,1.2),(177.3,1.8))],
 'Jecy Gold':[(0,(47.4,.2),(85.5,.9),(65.3,.6),(181.5,4.4)),(1,(48.1,.2),(84.8,.6),(73.0,1.3),(203.8,4.7)),(2,(48.0,.2),(84.3,.5),(70.8,1.2),(216.4,3.8)),(3,(49.9,.2),(84.1,.6),(70.3,1.0),(212.0,3.8))]
}
for cultivar,entries in j5.items():
 for spr,*vals in entries:
  for tissue,(val,se) in zip(['core','inner_pericarp','outer_pericarp_small','outer_pericarp_large'],vals):
   add('JEON2024',K2,cultivar,'fruit',tissue,'cell_mean_diameter',val,'µm',se=se,n=10,stage='harvest_180_DAA',treatment=f'BenefitsPZ_sprays={spr}',locator='Table 5, publisher HTML, 2024',note='Mean ± SE, 10 tissue samples per treatment; measured using dyed 5-µm histological sections. Outer pericarp distinct small/large cell populations.')

# Verify hardcoded source values/treatment/ranges
assert len(rows)==(6+4+3+36+30+30+32+32+32),len(rows)
assert len(set(r['id'] for r in rows))==len(rows)
assert all(r['unit'] in ['µm','mm','cm','g','count'] for r in rows)
assert len({r['id'] for r in rows if r['source_id']=='JAMES1974'})==13
assert sum(r['source_id']=='JEON2024' for r in rows)==96
assert any(r['metric']=='achene_total_per_fruit' and r['cultivar']=='Camarosa' and r['value']==325.6 for r in rows)
assert any(r['source_id']=='JEON2024' and r['metric']=='cell_mean_diameter' and r['cultivar']=='Sweet Gold' and r['treatment']=='BenefitsPZ_sprays=0' and r['tissue']=='core' and r['value']==47.3 for r in rows)

output={
 'schema_version':'fruit_morphometry.1',
 'prepared':'2026-11-20',
 'project':'Dmitry-dev-pet/strawberry-lab',
 'scope':'PRIMARY NUMERIC TABLES ONLY; observations specific to cultivar, stage, treatment; source extracted text vs PDF page-image confirmation status noted.',
 'units':'Preserve original source units, no conversion or invented Blender-world scale at this stage.',
 'sources':sources,
 'observations':rows,
 'limitations':[
 'Exact PDF screenshots of James and Currie failed due to cache miss; all PDF numbers were checked in parsed full text, but not directly against page bitmaps.',
 'ARIZA2011 original journal Table 2 was read from hosted full-text copy rather than publisher rendering.',
 'CURRIE1997 Chapter 3 cultivar not independently attested by nearby methods in parsed text: cultivar_unverified_ch3 is intentional; do not assign Hayward without confirmation.',
 'JEON2024 is A. chinensis var. chinensis, not green Hayward A. deliciosa; spray treatments are not baseline controls.',
 'Counts within sampled area or radial transect must never be treated as total cells of the fruit.',
 'No reliable fruit vascular diameter, exact strawberry cuticle thickness in a primary table, or region-resolved strawberry ripe-cell table extracted here; leave model parameters uncalibrated.',
 'No direct transfer of historical embryological stage means or treated experimental fruit measurements into a universal cultivar preset.'
 ]
}
out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
headers=['id','source_id','source_locator','taxon','cultivar','organ','tissue','metric','axis','stage','treatment','value','unit','uncertainty_value','uncertainty_kind','n','statistic','evidence','usage','note','source_url']
with (root/'measurements-v1.csv').open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=headers)
 writer.writeheader()
 for row in rows:writer.writerow({**row,'source_url':sources[row['source_id']]['url']})
print('DATASET',len(rows),'rows; breakdown:',dict(Counter(r['source_id'] for r in rows)),'JSON bytes',out.stat().st_size)