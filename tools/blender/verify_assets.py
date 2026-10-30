"""Independent export and route smoke checks, run with Blender in background."""
import json
import hashlib
import math
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_scene import check_scene

OUT=Path(__file__).resolve().parents[2]/'assets'/'airport'
manifest=json.loads((OUT/'manifest.json').read_text())
expected=['aircraft-narrowbody.glb','aircraft-widebody.glb','tower.glb',
          'runway-07L-25R.glb','runway-07C-25C.glb','runway-07R-25L.glb',
          'runway-18.glb','airport-environment.glb','airport-traffic-demo.glb']
report={'assets':[], 'checks':[]}
for filename in expected:
    path=OUT/'exports'/filename
    raw=path.read_bytes()
    magic,version,length=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and length==len(raw),filename
    json_length,chunk_type=struct.unpack_from('<II',raw,12)
    assert chunk_type==0x4E4F534A
    doc=json.loads(raw[20:20+json_length])
    assert not any('uri' in b for b in doc.get('buffers',[])),filename
    assert not any('uri' in image for image in doc.get('images',[])),filename
    for n in doc.get('nodes',[]):
        for key in ('translation','rotation','scale','matrix'):
            assert all(math.isfinite(v) for v in n.get(key,[])),(filename,key)
    triangles=0
    for m in doc['meshes']:
        for p in m['primitives']:
            count=doc['accessors'][p['indices']]['count'] if 'indices' in p else doc['accessors'][p['attributes']['POSITION']]['count']
            assert p.get('mode',4)==4,filename
            triangles+=count//3
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert meshes,filename
    verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    assert all(math.isfinite(c) for v in verts for c in v),filename
    bounds=[[round(min(v[i] for v in verts),4),round(max(v[i] for v in verts),4)] for i in range(3)]
    dims=[b-a for a,b in bounds]
    if filename.startswith('aircraft-'):
        nominal=37.6 if 'narrowbody' in filename else 64
        assert abs(dims[1]-nominal)<.3,(filename,dims)
        assert abs(bounds[2][0])<.12,(filename,'wheel-ground',bounds)
        for name in ('Nose','Left','Right'):
            assert any(o.type=='EMPTY' and o.name.startswith('Gear.'+name) for o in bpy.context.scene.objects)
    if filename.startswith('runway-'):
        nominal=2800 if '07L' in filename else 4000
        assert abs(dims[1]-(nominal+20))<1,(filename,dims)
    if filename=='airport-traffic-demo.glb':
        assert doc.get('animations'),filename
        assert len([o for o in bpy.context.scene.objects if o.name.startswith('Flight.') and o.type=='EMPTY'])==4
    assert len(raw)<15_000_000,(filename,'size budget')
    report['assets'].append({'file':filename,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles_unique':triangles,
        'mesh_nodes':len(meshes),'dimensions_blender_m':dims,'reimport':'passed',
        'animation_clips':len(doc.get('animations',[]))})
report['checks']+=['9 GLBs reimport successfully','All geometry finite','Self-contained buffers',
    'Aircraft lengths and ground contact','Three landing gear groups per aircraft','Runway lengths',
    'Traffic animation present','Each file smaller than 15 MB']

runways=manifest['runways']
assert set(runways)=={'north','center','south','west'}
assert all(runways[k]['heading']==70 for k in ('north','center','south'))
assert runways['west']['heading']==180
for phase in manifest['demonstration_phases']:
    direction=1 if phase['od']=='07' else -1
    for key in ('arrive_north','arrive_south','depart_center'):
        points=phase['paths'][key]
        v=Vector(points[-1])-Vector(points[-2])
        assert v.x*direction>0 and v.y*direction>0,(phase,key)
    flexible=phase['paths']['depart_flex']
    if phase['runway_18_usable']:
        assert abs(flexible[-1][0]-flexible[-2][0])<1e-5
        assert flexible[-1][1]<flexible[-2][1]
    else:
        assert flexible[-3:-1]==phase['paths']['depart_center'][-3:-1]
report['checks']+=['All three parallel runways share OD','18 departures always southbound',
                  '18 closure redirects the flexible departure to the centre runway']

# Verify the native project, including evaluated playback at every phase.
bpy.ops.wm.open_mainfile(filepath=str(OUT/'fra-airport.blend'))
s=bpy.data.scenes['FRA · Airport demonstration'];bpy.context.window.scene=s
for f in (1,600,1200,1201,1800,2400,2401,3000,3600):
    s.frame_set(f)
    active=[o for o in s.objects if o.name.startswith('State.') and o.type=='EMPTY' and o.scale.x>.5]
    assert len(active)==1,(f,'state visibility')
    for o in s.objects:
        if o.name.startswith('Flight.') and o.type=='EMPTY':
            assert all(math.isfinite(v) for v in o.location)
            assert o.location.z>=1.85-1e-5
report['checks'].append('Native scene opens; playback states and aircraft transforms valid')
report['scene_checks']=check_scene(s,manifest)
scene_failures=[message for message in report['scene_checks'] if message.startswith('FAIL:')]
if scene_failures:
    report['result']='failed'
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    raise AssertionError('\n'.join(scene_failures))

# Raycast the generated surfaces, not route metadata: every ground movement
# sample must actually sit on a runway or the unioned apron/taxi mesh.
surfaces=[]
for o in s.objects:
    if o.type!='MESH':continue
    if o.parent and o.parent.name=='Surface.TaxiApron':surfaces.append(o)
    elif o.parent and o.parent.name in [v['root'] for v in runways.values()]:
        if any(m and m.name.startswith('Runway ·') for m in o.data.materials):surfaces.append(o)
vertices=[]; faces=[]
for o in surfaces:
    offset=len(vertices)
    vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
    faces.extend(tuple(offset+i for i in face.vertices) for face in o.data.polygons)
surface_tree=BVHTree.FromPolygons(vertices,faces)
ground_samples=0
for f in range(1,s.frame_end+1):
    s.frame_set(f)
    for o in s.objects:
        if o.type!='EMPTY' or not o.get('demo_role'):continue
        p=o.matrix_world.translation
        if abs(p.z-1.85)<.005:
            hit=surface_tree.ray_cast(p+Vector((0,0,1)),Vector((0,0,-1)),1.15)
            assert hit[0] is not None,(f,o.name,'ground route leaves paved movement surface',list(p))
            assert abs(hit[0].z-1.85)<.01,(f,o.name,'surface height mismatch',hit[0].z)
            ground_samples+=1
report['checks'].append(f'{ground_samples} ground positions raycast onto actual movement pavement at z=1.85')
report['blend_sha256']=hashlib.sha256((OUT/'fra-airport.blend').read_bytes()).hexdigest()
report['result']='passed'
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
