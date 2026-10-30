"""Build the editable FRA library, GLB assets and previews in Blender.

Run: blender --background --threads 6 --python tools/blender/build_airport.py
Optional arguments after --: --no-render, --preview-only, --samples 32
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geometry import (palette, root, box, cylinder, sphere, beam, line, text,
                      mesh, aircraft, tower, runway, pavement)

OUT = HERE.parents[1] / 'assets' / 'airport'
EXPORT = OUT / 'exports'
PREVIEW = OUT / 'previews'
for folder in (OUT, EXPORT, PREVIEW):
    folder.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--no-render', action='store_true')
parser.add_argument('--preview-only', action='store_true')
parser.add_argument('--samples', type=int, default=40)
parser.add_argument('--preview-filter', default='')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])


def scene(name):
    s=bpy.data.scenes.new(name)
    bpy.context.window.scene=s
    s.unit_settings.system='METRIC'
    s.render.engine='CYCLES'
    s.cycles.samples=args.samples
    s.cycles.use_denoising=True
    s.render.resolution_x=1600
    s.render.resolution_y=1100
    s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'
    s.view_settings.view_transform='AgX'
    s.view_settings.exposure=.45
    s.world=bpy.data.worlds.new(name+' World')
    s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.73,.80,.86,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    s.render.fps=24
    return s


def descendants(o):
    return [o]+list(o.children_recursive)


def consolidate(r):
    """Bake bevels and merge static material groups, preserving articulated roots."""
    groups={}
    for o in list(r.children_recursive):
        if o.type not in ('MESH','CURVE','FONT'): continue
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active=o
        if o.type!='MESH':
            bpy.ops.object.convert(target='MESH')
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        bm.to_mesh(o.data);bm.free()
        key=(o.parent,tuple(o.data.materials))
        groups.setdefault(key,[]).append(o)
    for (parent,mats),objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.join()
        o=bpy.context.object
        o.name=parent.name+'.'+(mats[0].name.split(' · ')[0] if mats else 'Mesh')
    bpy.ops.object.select_all(action='DESELECT')


def clone(source,name,location=(0,0,0),scale=1,heading=0):
    mapping={}
    for old in descendants(source):
        new=old.copy()
        new.animation_data_clear()
        bpy.context.collection.objects.link(new)
        mapping[old]=new
    for old,new in mapping.items():
        new.parent=mapping.get(old.parent)
    r=mapping[source]
    r.name=name
    r.location=location
    r.scale=(scale,scale,scale) if isinstance(scale,(float,int)) else scale
    r.rotation_euler.z=-math.radians(heading)
    return r


def camera(name,position,target,scale):
    bpy.ops.object.camera_add(location=position)
    c=bpy.context.object;c.name=name
    c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
    c.data.type='ORTHO';c.data.ortho_scale=scale;c.data.lens=50
    c.data.clip_end=10000
    return c


def lighting(s,size):
    bpy.ops.object.light_add(type='AREA', location=(-size*.3,-size*.5,size*.9))
    o=bpy.context.object;o.name='Studio softbox'
    o.data.energy=size*size*4
    o.data.shape='DISK';o.data.size=size*.7
    o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='SUN',location=(0,0,size))
    o=bpy.context.object;o.name='Soft afternoon sun'
    o.data.energy=1.5;o.data.angle=math.radians(14)
    o.rotation_euler=(math.radians(25),math.radians(-18),math.radians(-30))


def studio(s,r,m,position,target,scale):
    ground=box('Studio floor',(0,0,-.16),(6000,6000,.25),m['paper'],edge=.05)
    s.camera=camera('Camera · product',position,target,scale)
    lighting(s,scale)


def export_glb(s,r,name,animated=False):
    bpy.context.window.scene=s
    bpy.ops.object.select_all(action='DESELECT')
    for o in descendants(r):o.select_set(True)
    bpy.context.view_layer.objects.active=r
    bpy.ops.export_scene.gltf(filepath=str(EXPORT/name),export_format='GLB',
        use_selection=True,export_yup=True,export_apply=True,
        export_animations=animated,export_extras=True,export_cameras=False,
        export_lights=False,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')


def render(s,name,cam=None,frame=1):
    if args.preview_filter and name not in args.preview_filter.split(','):
        return
    bpy.context.window.scene=s
    s.cycles.samples=args.samples
    s.frame_set(frame)
    if cam:s.camera=cam
    s.render.filepath=str(PREVIEW/name)
    bpy.ops.render.render(write_still=True)


from airport_scene import airport_layout, animate_demo


if not args.preview_only:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m=palette();assets={};asset_scenes={}
    for key,wide in [('narrowbody',False),('widebody',True)]:
        s=scene('Asset · '+key.title())
        r=aircraft('Aircraft.'+key,m,wide)
        consolidate(r);assets[key]=r;asset_scenes[key]=s
        export_glb(s,r,'aircraft-'+key+'.glb')
        k=1.65 if wide else 1
        studio(s,r,m,(43*k,57*k,31*k),(0,0,3.8*k),53*k)
    s=scene('Asset · Tower');r=tower(m);consolidate(r)
    assets['tower']=r;asset_scenes['tower']=s
    export_glb(s,r,'tower.glb')
    studio(s,r,m,(-95,-130,92),(0,0,34),124)
    for key,length,width,labels,heading in [
        ('07L-25R',2800,45,('07L','25R'),70),('07C-25C',4000,60,('07C','25C'),70),
        ('07R-25L',4000,45,('07R','25L'),70),('18',4000,45,('18',''),180)]:
        s=scene('Asset · Runway '+key)
        r=runway('Runway.'+key,m,length,width,labels,heading);consolidate(r)
        assets[key]=r;asset_scenes[key]=s
        export_glb(s,r,'runway-'+key+'.glb')
        studio(s,r,m,(180,-length/2-260,350),(0,-length/2+220,0),650)
    s=scene('FRA · Airport demonstration')
    env,specs=airport_layout(m,assets,clone);consolidate(env)
    export_glb(s,env,'airport-environment.glb')
    demo,routes=animate_demo(s,assets,specs,m,clone)
    export_glb(s,demo,'airport-traffic-demo.glb',True)
    box('Studio background',(0,0,-12),(5000,5000,4),m['paper'],edge=2)
    lighting(s,850)
    cam=camera('Camera · airport overview',(660,-1000,1550),(0,-55,0),1180)
    s.camera=cam
    camera('Camera · terminal detail',(110,-190,290),(-45,120,15),400)
    camera('Camera · top plan',(0,-55,1400),(0,-55,0),1220)
    s['README']='Three illustrative states; markers at 1, 481, 961. Space plays. Models in Asset scenes.'
    s['forecast_contract']='web/src/lib/forecast-types.ts; animations are fixtures, not forecast output.'
    # Friendly initial viewport: camera composition in solid material colour.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.color_type='MATERIAL'
                area.spaces.active.clip_end=10000
                area.spaces.active.overlay.show_overlays=False
    manifest={'version':2,'blender_version':bpy.app.version_string,
        'coordinate_system':{'blend':{'up':'+Z','north':'+Y','east':'+X','aircraft_forward':'+Y'},
                             'glb':{'up':'+Y','north':'-Z','east':'+X','aircraft_forward':'-Z'},
                             'point_conversion':'[x, y, z] in Blender -> [x, z, -y] in glTF'},
        'asset_units':'metres','airport_layout':'illustrative compressed diagram, not georeferenced',
        'display_scale':{'runway_length':.12,'runway_width':.30,'tower':.70,
                         'moving_narrowbody':.60,'moving_widebody':.42,'parked_narrowbody':.42},
        'surface_levels':{'landscape':.7,'movement_surface':1.85,'taxi_paint':1.895,'route_highlight':1.98},
        'runway_obstacle_clearance':12,'runways':specs,'fps':24,'demonstration_phases':routes,
        'integration':{'od':'HourForecast.od (one shared value for all parallel runways)',
           'runway18':'HourForecast.p_18_usable (show probability; a binary display threshold is a UI policy)',
           'certainty':'HourForecast.certainty; not aircraft-assignment confidence',
           'no_model_inference':'Paths are illustrative fixtures, not ATC decisions or forecast outputs.'}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'fra-airport.blend'))
else:
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'fra-airport.blend'))

if not args.no_render:
    for name,file in [('Asset · Narrowbody','aircraft-narrowbody.png'),
                       ('Asset · Widebody','aircraft-widebody.png'),('Asset · Tower','tower.png'),
                       ('Asset · Runway 07C-25C','runway-detail.png')]:
        render(bpy.data.scenes[name],file)
    s=bpy.data.scenes['FRA · Airport demonstration']
    for frame,name in [(240,'airport-25.png'),(720,'airport-07.png'),(1260,'airport-18-closed.png')]:
        render(s,name,bpy.data.objects['Camera · airport overview'],frame)
    render(s,'terminal-detail.png',bpy.data.objects['Camera · terminal detail'],240)
    render(s,'airport-plan.png',bpy.data.objects['Camera · top plan'],240)
    s.camera=bpy.data.objects['Camera · airport overview'];s.frame_set(240)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'fra-airport.blend'))
print('FRA_ASSET_BUILD_COMPLETE', flush=True)
