"""Read-only dependency-key probe of the owner-provided reference archive.
Does not export any author code or node trees. This is an isolated key-function
probe, not a runtime test of the absent commercial Strawberry template.
"""
import ast
import copy
import hashlib
import json
import sys
import types
import zipfile
from pathlib import Path

PIN = 'aaa218470ab068ed1cb806308d9a4da1d43fd5d9e3de30f6486ac7d204787877'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(archive, runtime):
    assert sha(archive) == PIN
    with zipfile.ZipFile(archive) as z:
        trees = {n: ast.parse(z.read(n + '.py').decode('utf-8')) for n in ('fruechte', 'spawn', 'leitbuendel')}
    def literal(mod, name):
        a = next(n for n in trees[mod].body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
        return ast.literal_eval(a.value)
    def function(mod, name, env, drop_imports=False):
        n = copy.deepcopy(next(n for n in trees[mod].body if isinstance(n, ast.FunctionDef) and n.name == name))
        # Only the pure state/key computation is exercised; the relative
        # fruechte import is replaced by the explicit minimal context below.
        if drop_imports:
            n.body = [x for x in n.body if not isinstance(x, (ast.Import, ast.ImportFrom))]
        exec(compile(ast.fix_missing_locations(ast.Module(body=[n], type_ignores=[])), mod+'.py', 'exec'), env)
        return env[name]
    shape = literal('fruechte', 'ERDBEERE_FORM')
    extra = literal('fruechte', 'ERDBEERE_EXTRA')
    shape_names = {e[0] for e in shape if e[0] != 'seed'} | {'typ_nr'}
    classes = {e[0]: e[4] for e in extra}
    f = types.SimpleNamespace(form_null={k: 0 for k in shape_names}, klassen=classes, kelch_felder=('krone_groesse','krone_staerke','krone_weich'))
    klass = function('fruechte', 'klasse', {})
    level = [40.0]
    context = types.SimpleNamespace(aktuell=lambda: f, klasse=klass)
    keys = function('spawn', 'schluessel', {'json':json, 'fruechte':context, 'aufloesung':types.SimpleNamespace(prozent=lambda:level[0])})
    # STANDARD in this source is a dict(...) call, not an ast literal.
    v = next(n.value for n in trees['leitbuendel'].body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STANDARD' for t in n.targets))
    assert isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='dict' and not v.args
    vessel_defaults = {k.arg:ast.literal_eval(k.value) for k in v.keywords}
    vessel_key = function('leitbuendel','schluessel',{})
    state = {'form':{**{e[0]: (e[6] if len(e)>6 else 0.0) for e in shape if e[0]!='seed'}, 'typ_nr':0.0, **{e[0]:e[5] for e in extra}},'seed':0,'seed_blatt':0,'blatt':{}}
    def four(s):
        return (*keys(s),vessel_key({k:s['form'].get(k,x) for k,x in vessel_defaults.items()}))
    base = four(state)
    result = {}
    for k in sorted(state['form']):
        s=copy.deepcopy(state);s['form'][k]+=0.5
        result[k]={'class':klass(f,k),'changed_keys':[a for a,x,y in zip(('exterior','leaves','flesh_form','vascular'),base,four(s)) if x!=y]}
    for k in ('seed','seed_blatt'):
        s=copy.deepcopy(state);s[k]+=1
        result[k]={'class':'state','changed_keys':[a for a,x,y in zip(('exterior','leaves','flesh_form','vascular'),base,four(s)) if x!=y]}
    level[0]=50
    result['resolution']={'class':'global','changed_keys':[a for a,x,y in zip(('exterior','leaves','flesh_form','vascular'),base,four(state)) if x!=y]}
    level[0]=40
    assert result['laenge']['changed_keys']==['flesh_form']
    assert result['kern_anzahl']['changed_keys']==['exterior','flesh_form']
    assert result['leit_straenge']['changed_keys']==['vascular']
    assert result['haut_glanz']['changed_keys']==[]
    assert result['krone_groesse']['changed_keys']==['exterior','leaves','flesh_form']
    assert result['hoehle']['changed_keys']==['flesh_form']
    assert result['resolution']['changed_keys']==['exterior','leaves']
    r=json.loads(Path(runtime).read_text());assert r['source_archive_sha256']==PIN
    obs={o['name']:{k:o[k] for k in ('body_vertices','body_faces','basis_valid','inside_valid','dimensions')} for o in r['observations']}
    graphs=r['graph_inventory']['objects']; byname={o['object']:o['modifiers'] for o in graphs}
    skin=next(m for m in byname['SCHNELL KIWI | Körper'] if m['modifier']=='Live')['sdf']
    flesh=byname['SCHNELL KIWI | Schnittfläche'][0]['sdf']
    assert skin['GeometryNodeSampleGrid']==1 and 'GeometryNodeGridToMesh' not in skin
    assert flesh['GeometryNodeSDFGridBoolean']==1 and flesh['GeometryNodeGridToMesh']==1
    return {'archive_sha256':PIN,'prior_runtime_receipt_sha256':sha(runtime),'method':'Isolated execution of three unmodified source key/class functions with minimal mocked species/resolution context; source code not exported. No commercial template executed. Previous Kiwi runtime receipt read and cross-checked, not rerun.', 'parameter_count':len(result),'parameter_keys':result,'derived_invalidation_note':'jobs._frei_starten also rebuilds interior when exterior changes, and may rebuild foliage for a referenced stand. Key comparison is not the full invalidation scheduler.', 'kiwi_prior_observations':obs,'kiwi_prior_skin_live_counts':skin,'kiwi_prior_flesh_cut_counts':flesh, 'exact_rotation_geometry_confirmed':r['exact_plane_rotation_geometry_confirmed']}

if __name__=='__main__':
    out=Path(sys.argv[3]); assert not out.exists()
    out.write_text(json.dumps(probe(sys.argv[1],sys.argv[2]),indent=2,ensure_ascii=False)+'\n')
