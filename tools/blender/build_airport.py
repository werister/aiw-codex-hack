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


def airport_layout(m,assets):
    r=root('Airport.Environment',kind='illustrative_airport',units='display_metres',
           geospatial=False,north='+Y',east='+X')
    box('Landscape plinth',(0,-55,-5),(820,670,10),m['base'],r,20)
    box('Landscape surface',(0,-55,-.8),(818,668,3),m['grass'],r,18)
    # HACK: compressed schematic footprint keeps all four runways legible in the demo.
    specs={
        'north':{'center':(-95,174),'heading':70,'length':336,'width':13.5,'asset':'07L-25R','role':'landing'},
        'center':{'center':(62,21),'heading':70,'length':480,'width':18,'asset':'07C-25C','role':'departure'},
        'south':{'center':(70,-64),'heading':70,'length':480,'width':13.5,'asset':'07R-25L','role':'landing'},
        'west':{'center':(-275,-125),'heading':180,'length':480,'width':13.5,'asset':'18','role':'departure'},
    }
    for key,spec in specs.items():
        x,y=spec['center']
        runway_obj=clone(assets[spec['asset']], 'Runway.'+key,(x,y,1.5),(.30,.12,1),spec['heading'])
        runway_obj.parent=r
        spec['root']=runway_obj.name
        # A short label outside each runway survives map-scale rendering.
        label=spec['asset'].replace('-',' / ')
        text('Runway caption',label,(x+20,y+16,2),7.5,m['white'],r)
    # Taxi network and apron are original illustrative geometry, not surveyed routes.
    box('Main apron',(48,101,1.1),(370,85,.8),m['apron'],r,8)
    for yy in (62,-22):
        o=box('Parallel taxiway',(60,yy,1.4),(490,8,.5),m['shoulder'],r,3)
        o.rotation_euler.z=math.radians(20)
        line('Taxi guidance',[(-165,yy-82,1.75),(288,yy+83,1.75)],.32,m['yellow'],r)
    for x in (-140,-38,160,280):
        pavement('Taxi connector',[(x,95,1.65),(x,38,1.65),(x+15,-11,1.65)],8,m['shoulder'],r)
        line('Taxi center',[(x,95,1.8),(x,38,1.8),(x+15,-11,1.8)],.3,m['yellow'],r)
    pavement('West connector',[(-140,86,1.6),(-230,86,1.6),(-275,114,1.6)],10,m['shoulder'],r)
    line('West centerline',[(-140,86,1.9),(-230,86,1.9),(-275,114,1.9)],.3,m['yellow'],r)
    # Use the same curves for demonstration motion and its paved connectors.
    for layer,od in enumerate(('07','25')):
        taxi=routes_for(specs,od,True)['depart_center'][:-2]
        points=[(v.x,v.y,1.76+layer*.025) for v in fillet(taxi)]
        pavement('Departure taxi connector',points,9,m['shoulder'],r)
        line('Departure taxi guide',[(x,y,1.94) for x,y,z in points],.27,m['yellow'],r)
    pavement('Apron west link',[(-160,86,1.76),(30,81,1.76)],9,m['shoulder'],r)
    line('Apron west guide',[(-160,86,1.94),(30,81,1.94)],.27,m['yellow'],r)
    # Terminal: matte roof, glass band, roof ribs, articulated gate bridges.
    box('Terminal glazing',(60,131,9),(240,24,14),m['glass'],r,2)
    box('Terminal podium',(60,131,3),(245,27,3),m['concrete'],r,2)
    box('Terminal roof',(60,131,17),(248,29,2),m['concrete'],r,2)
    for x in range(-50,181,12):
        box('Roof rib',(x,131,18.2),(1.4,27,.9),m['roof'],r,.3)
        box('Facade mullion',(x,118.8,10),(.4,.5,12),m['concrete'],r)
    for x in (-25,60,145):
        box('Concourse',(x,104,9),(12,38,12),m['concrete'],r,1)
        box('Concourse glazing',(x,104,10),(12.2,32,5),m['glass'],r,.2)
        box('Concourse roof',(x,104,15.7),(14,40,1.5),m['roof'],r,1)
        for sign in (-1,1):
            box('Jet bridge',(x+sign*12,95,6),(14,3.8,4),m['concrete'],r,.5)
            box('Bridge glazing',(x+sign*12,92.9,6.5),(12,.1,2),m['glass'],r)
        for j in (-1,1):
            line('Stand lead-in',[(x+j*22,76,1.8),(x+j*22,99,1.8)],.25,m['yellow'],r)
    tr=clone(assets['tower'],'Tower.Airport',(-120,108,1.5),.9);tr.parent=r
    for x,y,w,d in ((220,155,60,30),(285,175,42,24),(-155,-90,48,30)):
        box('Service building',(x,y,7),(w,d,11),m['concrete'],r,1.5)
        box('Service roof',(x,y,13),(w+2,d+2,1.4),m['roof'],r,.8)
        for xx in range(int(x-w/2)+6,int(x+w/2),10):
            box('Service bay',(xx,y-d/2-.1,6),(6,.2,6),m['glass'],r,.3)
    # Restrained vegetation, with clear space around pavement and approaches.
    rng=random.Random(18)
    for j in range(145):
        x,y=rng.uniform(-386,382),rng.uniform(-362,253)
        clear=any(abs(x-spec['center'][0])<35 and key=='west' for key,spec in specs.items())
        for key,spec in specs.items():
            if key=='west':continue
            dx,dy=x-spec['center'][0],y-spec['center'][1]
            cross=abs(dx*math.cos(math.radians(70))-dy*math.sin(math.radians(70)))
            along=abs(dx*math.sin(math.radians(70))+dy*math.cos(math.radians(70)))
            if cross<38 and along<spec['length']/2+70:clear=True
        if clear or (-190<x<335 and 48<y<205):continue
        h=rng.uniform(4.5,9)
        cylinder('Tree trunk',(x,y,2.5),.45,3,m['concrete'],r,8)
        sphere('Tree canopy',(x,y,h*.65+2),(h*.42,h*.42,h*.58),m['tree' if j%2 else 'tree2'],r)
    text('Ground title','F R A',(237,-286,1.7),25,m['white'],r)
    text('Ground subtitle','OPERATING DIRECTION', (237,-309,1.7),5.5,m['white'],r)
    text('Schematic note','SCHEMATIC AIRFIELD', (237,-321,1.7),4,m['white'],r)
    line('North stem',[(345,205,2),(345,237,2)],.55,m['white'],r)
    mesh('North arrow',[(345,245,2),(339,233,2),(351,233,2)],[(0,1,2)],m['white'],r)
    text('North letter','N',(345,253,2),7,m['white'],r)
    return r,specs


def runway_point(spec,along,height=2):
    a=math.radians(spec['heading'])
    return (spec['center'][0]+math.sin(a)*along,spec['center'][1]+math.cos(a)*along,height)


def routes_for(specs,od,usable):
    direction=1 if od=='07' else -1
    routes={}
    for key in ('north','south'):
        s=specs[key];half=s['length']/2
        routes['arrive_'+key]=[runway_point(s,-direction*(half+100),30),
              runway_point(s,-direction*(half-25),2),runway_point(s,direction*(half-65),2)]
    s=specs['center'];half=s['length']/2
    entry=runway_point(s,-direction*(half-16),2)
    taxi_y=lambda x:62+(x-60)*math.tan(math.radians(20))
    routes['depart_center']=[(30,81,2),(30,taxi_y(30),2),(entry[0],taxi_y(entry[0]),2),entry,
            runway_point(s,direction*110,2),runway_point(s,direction*(half+105),38)]
    if usable:
        s=specs['west'];half=s['length']/2
        routes['depart_flex']=[(-160,86,2),(-230,86,2),(-275,114,2),runway_point(s,-half+16,2),
             runway_point(s,110,2),runway_point(s,half+75,38)]
    else:
        routes['depart_flex']=[(-160,86,2)]+routes['depart_center']
    return routes


def fillet(points):
    """Quadratic corners keep taxi turns readable; runway legs remain straight."""
    result=[Vector(points[0])]
    for i in range(1,len(points)-1):
        a,b,c=map(Vector,points[i-1:i+2])
        d=min(12,(b-a).length*.18,(c-b).length*.18)
        entry=b+(a-b).normalized()*d
        end=b+(c-b).normalized()*d
        result.append(entry)
        for j in range(1,9):
            t=j/8
            result.append((1-t)**2*entry+2*(1-t)*t*b+t*t*end)
    result.append(Vector(points[-1]))
    return result


def sample(points,t):
    lengths=[(b-a).length for a,b in zip(points,points[1:])]
    remaining=t*sum(lengths)
    for i,d in enumerate(lengths):
        if remaining<=d or i==len(lengths)-1:
            u=min(1,max(0,remaining/d))
            return points[i].lerp(points[i+1],u),points[i+1]-points[i]
        remaining-=d


def animate_demo(s,assets,env,specs,m):
    demo=root('Airport.Demonstration',kind='illustrative_animation',forecast_connected=False)
    phases=[('25',True),('07',True),('07',False)]
    planes={}
    for key,asset in [('arrive_north','narrowbody'),('arrive_south','widebody'),
                      ('depart_center','narrowbody'),('depart_flex','narrowbody')]:
        p=clone(assets[asset],'Flight.'+key,scale=.55 if asset=='widebody' else .70)
        p.parent=demo;planes[key]=p
    all_routes=[]
    for phase,(od,usable) in enumerate(phases):
        start=phase*240+1
        routes=routes_for(specs,od,usable)
        all_routes.append({'start_frame':start,'end_frame':start+239,'od':od,'runway_18_usable':usable,
             'paths':{k:[list(p) for p in v] for k,v in routes.items()}})
        s.timeline_markers.new('OD '+od+' · RWY 18 '+('OPEN' if usable else 'CLOSED'),frame=start)
        for key,p in planes.items():
            points=fillet(routes[key]);last_yaw=None
            for frame in range(start,start+240):
                # Two centre departures are staggered in the closure demonstration.
                t=(frame-start)/239
                if not usable and key=='depart_flex':t=max(0,t-.40)
                pos,tangent=sample(points,t)
                yaw=math.atan2(-tangent.x,tangent.y)
                if last_yaw is not None:
                    while yaw-last_yaw>math.pi:yaw-=math.tau
                    while yaw-last_yaw<-math.pi:yaw+=math.tau
                last_yaw=yaw
                p.location=pos
                p.rotation_euler=(math.atan2(tangent.z,math.hypot(tangent.x,tangent.y)),0,yaw)
                p.keyframe_insert(data_path='location',frame=frame)
                p.keyframe_insert(data_path='rotation_euler',frame=frame)
    # Separate status objects and direction arrows are easy for the web owner to drive.
    for phase,(od,usable) in enumerate(phases):
        overlay=root('State.'+str(phase+1),od=od,runway_18_usable=usable)
        overlay.parent=demo
        for key,spec in specs.items():
            if key=='west' and not usable:
                x,y=spec['center']
                for sign in (-1,1):
                    line('Closed cross',[(x-5,y-5*sign,3),(x+5,y+5*sign,3)],.75,m['red'],overlay)
                continue
            heading=180 if key=='west' else (70 if od=='07' else 250)
            x,y=spec['center'];a=math.radians(heading)
            tip=Vector((math.sin(a),math.cos(a),0));side=Vector((tip.y,-tip.x,0))
            c=Vector((x,y,2.3))
            mat=m['green'] if key=='west' else m['blue']
            line('Direction shaft',[c-tip*19,c+tip*19],1,mat,overlay)
            mesh('Direction head',[c+tip*29,c+tip*14+side*5,c+tip*14-side*5],[(0,1,2)],mat,overlay)
        for f in (1,240,241,480,481,720):
            active=(f-1)//240==phase
            overlay.scale=(1,1,1) if active else (0,0,0)
            overlay.keyframe_insert(data_path='scale',frame=f)
    s.frame_start=1;s.frame_end=720;s.frame_set(125)
    return demo,all_routes


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
    env,specs=airport_layout(m,assets);consolidate(env)
    # Parked aircraft are linked geometry with independently selectable roots.
    for i,(x,y) in enumerate([(-48,92),(-1,92),(37,92),(84,92),(122,92),(169,92)]):
        p=clone(assets['narrowbody'],'Parked.'+str(i+1),(x,y,1.9),.48,180)
        p.parent=env
    export_glb(s,env,'airport-environment.glb')
    demo,routes=animate_demo(s,assets,env,specs,m)
    export_glb(s,demo,'airport-traffic-demo.glb',True)
    box('Studio background',(0,0,-12),(5000,5000,4),m['paper'],edge=2)
    lighting(s,850)
    cam=camera('Camera · airport overview',(900,-1150,1100),(0,-55,0),1180)
    s.camera=cam
    camera('Camera · terminal detail',(190,-195,220),(-30,90,15),360)
    camera('Camera · top plan',(0,-55,1400),(0,-55,0),930)
    s['README']='Three illustrative states; markers at 1, 241, 481. Space plays. Models in Asset scenes.'
    s['forecast_contract']='web/src/lib/forecast-types.ts; animations are fixtures, not forecast output.'
    # Friendly initial viewport: camera composition in solid material colour.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.color_type='MATERIAL'
                area.spaces.active.clip_end=10000
                area.spaces.active.overlay.show_overlays=False
    manifest={'version':1,'blender_version':bpy.app.version_string,
        'coordinate_system':{'blend':{'up':'+Z','north':'+Y','east':'+X','aircraft_forward':'+Y'},
                             'glb':{'up':'+Y','north':'-Z','east':'+X','aircraft_forward':'-Z'},
                             'point_conversion':'[x, y, z] in Blender -> [x, z, -y] in glTF'},
        'asset_units':'metres','airport_layout':'illustrative compressed diagram, not georeferenced',
        'display_scale':{'runway_length':.12,'runway_width':.30,'tower':.9,
                         'moving_narrowbody':.70,'moving_widebody':.55,'parked_narrowbody':.48},
        'runways':specs,'fps':24,'demonstration_phases':routes,
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
    for frame,name in [(125,'airport-25.png'),(365,'airport-07.png'),(605,'airport-18-closed.png')]:
        render(s,name,bpy.data.objects['Camera · airport overview'],frame)
    render(s,'terminal-detail.png',bpy.data.objects['Camera · terminal detail'],125)
    render(s,'airport-plan.png',bpy.data.objects['Camera · top plan'],125)
    s.camera=bpy.data.objects['Camera · airport overview'];s.frame_set(125)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'fra-airport.blend'))
print('FRA_ASSET_BUILD_COMPLETE', flush=True)
