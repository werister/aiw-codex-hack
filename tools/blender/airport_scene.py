"""Compact airport layout: shared surfaces, clear corridors, three demo examples."""
import math
import random
import json
import subprocess
from pathlib import Path

import bpy
from mathutils import Vector

from geometry import root, box, cylinder, sphere, mesh, text

GROUND = 1.85
PHASE_FRAMES = 480
U = Vector((math.sin(math.radians(70)), math.cos(math.radians(70)), 0))
V = Vector((-U.y, U.x, 0))


def uv(u, v, z=GROUND):
    p = U*u + V*v
    return (p.x, p.y, z)


def runway_point(spec, along, height=GROUND):
    a = math.radians(spec['heading'])
    return (spec['center'][0]+math.sin(a)*along,
            spec['center'][1]+math.cos(a)*along, height)


def fillet(points):
    result = [Vector(points[0])]
    for i in range(1, len(points)-1):
        a, b, c = map(Vector, points[i-1:i+2])
        d = min(18, (b-a).length*.25, (c-b).length*.25)
        entry, end = b+(a-b).normalized()*d, b+(c-b).normalized()*d
        result.append(entry)
        for j in range(1, 13):
            t = j/12
            result.append((1-t)**2*entry + 2*(1-t)*t*b + t*t*end)
    result.append(Vector(points[-1]))
    return result


def sample(points, t):
    lengths = [(b-a).length for a,b in zip(points, points[1:])]
    remaining = max(0, min(1, t))*sum(lengths)
    for i,d in enumerate(lengths):
        if remaining <= d or i == len(lengths)-1:
            return points[i].lerp(points[i+1], min(1, remaining/d)), points[i+1]-points[i]
        remaining -= d


def strip_polygon(points, width):
    points = [Vector((p[0],p[1],0)) for p in points]
    normals = [Vector((b.y-a.y,a.x-b.x,0)).normalized() for a,b in zip(points,points[1:])]
    left, right = [], []
    for i,p in enumerate(points):
        before, after = normals[max(0,i-1)], normals[min(i,len(normals)-1)]
        n = (before+after).normalized()
        offset = n*(width/2/max(.4,n.dot(before)))
        left.append(p+offset); right.append(p-offset)
    return left + list(reversed(right))


def slab(name, polygon, bottom, top, mat, parent):
    verts = [(p[0],p[1],z) for z in (bottom,top) for p in polygon]
    n = len(polygon)
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o = mesh(name,verts,faces,mat,parent)
    # Input ribbons can have either winding. Exact booleans need outward normals.
    import bmesh
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def unified_surface(name, paths, width, bottom, top, mat, parent, specs=None, polygons=()):
    """2D union and constrained triangulation avoid coplanar boolean ambiguity."""
    cutouts=[]
    for spec in (specs or {}).values():
        a=math.radians(spec['heading'])
        along=Vector((math.sin(a),math.cos(a),0)); across=Vector((along.y,-along.x,0))
        center=Vector((*spec['center'],0))
        cutouts.append([list(center+along*x*(spec['length']/2+.01)+across*y*(spec['width']/2+.01))[:2]
                        for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]])
    here=Path(__file__).resolve().parent
    payload=dict(paths=[[[float(p[0]),float(p[1])] for p in path] for path in paths],
                 width=width,polygons=[[list(p)[:2] for p in poly] for poly in polygons],cutouts=cutouts)
    result=subprocess.run([str(here/'.venv/bin/python'),str(here/'surface_union.py')],
                          input=json.dumps(payload),text=True,capture_output=True,check=True)
    data=json.loads(result.stdout); n=len(data['vertices'])
    vertices=[(x,y,z) for z in (bottom,top) for x,y in data['vertices']]
    faces=[tuple(reversed(t)) for t in data['triangles']]
    faces += [tuple(i+n for i in t) for t in data['triangles']]
    for ring in data['boundaries']:
        faces += [(a,b,b+n,a+n) for a,b in zip(ring,ring[1:]+ring[:1])]
    o=mesh(name,vertices,faces,mat,parent)
    o['surface_top']=top
    o['plan_area']=data['area']
    return o


def routes_for(specs, od, usable):
    direction=1 if od=='07' else -1
    routes={}
    for key in ('north','south'):
        s=specs[key]; half=s['length']/2
        routes['arrive_'+key]=[
            runway_point(s,-direction*(half+85),32),
            runway_point(s,-direction*(half-28)),
            runway_point(s,direction*(half-60))]
    s=specs['center']; half=s['length']/2
    entry=runway_point(s,-direction*(half-18))
    # Parallel taxi lane is measured from the same runway axis as the entry.
    c=Vector((*s['center'],0)); lane=Vector(entry)+V*40
    start=uv(65,55)
    routes['depart_center']=[start,uv(65,40+c.dot(V)),tuple(lane),entry,
        runway_point(s,direction*110),runway_point(s,direction*(half+150),58)]
    if usable:
        s=specs['west']; half=s['length']/2
        start_flex=uv(-150,70)
        routes['depart_flex']=[start_flex,(-230,start_flex[1],GROUND),
            (-285,60,GROUND),runway_point(s,-half+17),
            runway_point(s,110),runway_point(s,half+75,40)]
    else:
        routes['depart_flex']=[uv(-150,70),uv(-150,40+c.dot(V)),tuple(lane),entry,
            runway_point(s,direction*110),runway_point(s,direction*(half+105),38)]
    return routes


def group(name, parent, kind=None):
    r=root(name)
    r.parent=parent
    if kind:r['obstacle_kind']=kind
    return r


def aligned_box(name,u,v,z,dims,mat,parent,edge=0):
    o=box(name,uv(u,v,z),dims,mat,parent,edge)
    o.rotation_euler.z=math.radians(20)
    return o


def airport_layout(m, assets, clone):
    env=root('Airport.Environment',kind='illustrative_airport',geospatial=False,
             units='display_metres',north='+Y',east='+X')
    ground=group('Landscape',env)
    box('Landscape plinth',(0,-55,-5),(900,800,10),m['base'],ground,18)
    box('Landscape surface',(0,-55,-.8),(898,798,3),m['grass'],ground,16)
    specs={
        'north':dict(center=(-95,174),heading=70,length=336,width=13.5,asset='07L-25R',role='landing'),
        'center':dict(center=(62,21),heading=70,length=480,width=18,asset='07C-25C',role='departure'),
        'south':dict(center=(70,-64),heading=70,length=480,width=13.5,asset='07R-25L',role='landing'),
        'west':dict(center=(-320,-125),heading=180,length=480,width=13.5,asset='18',role='departure'),
    }
    for key,spec in specs.items():
        r=clone(assets[spec['asset']],'Runway.'+key,(*spec['center'],1.5),(.30,.12,1),spec['heading'])
        r.parent=env; spec['root']=r.name
        offset=Vector((-31,0,0)) if key=='west' else -V*26
        p=Vector((*spec['center'],1.12))+offset
        text('Runway caption',spec['asset'].replace('-',' / '),p,7.3,m['white'],ground,
             math.radians(90) if key=='west' else math.radians(20))
    paths=[]
    for od in ('07','25'):
        paths.append(fillet(routes_for(specs,od,True)['depart_center'][:-2]))
    paths.append(fillet(routes_for(specs,'07',True)['depart_flex'][:-2]))
    paths.append(fillet(routes_for(specs,'07',False)['depart_flex'][:-2]))
    surface=group('Surface.TaxiApron',env)
    apron=[uv(u,v) for u,v in [(-205,42),(285,42),(285,153),(-205,153)]]
    unified_surface('Unified apron and taxiways',paths,15,1.25,GROUND,m['apron'],surface,specs,[apron])
    guides=group('Surface.TaxiPaint',env)
    unified_surface('Unified taxi centerlines',paths,.55,
                    GROUND+.015,GROUND+.045,m['yellow'],guides,specs)

    terminal=group('Building.Terminal',env,'building')
    aligned_box('Terminal podium',65,132,3.0,(242,27,3.1),m['concrete'],terminal,1.5)
    aligned_box('Terminal glazing',65,132,9,(238,24,14),m['glass'],terminal,1.5)
    aligned_box('Terminal roof',65,132,17,(244,29,2),m['concrete'],terminal,1.5)
    for u in range(-42,181,12):
        aligned_box('Roof rib',u,132,18.2,(1.3,27,.8),m['roof'],terminal,.2)
        aligned_box('Mullion',u,119.8,9,(.5,.5,12),m['concrete'],terminal)
    for u in (-15,65,145):
        concourse=group('Building.Concourse',env,'building')
        aligned_box('Concourse',u,101,8,(12,44,13),m['concrete'],concourse,1)
        aligned_box('Concourse glazing',u,101,10,(12.3,38,5),m['glass'],concourse,.2)
        aligned_box('Concourse roof',u,101,15,(14,46,1.5),m['roof'],concourse,.8)
        for sign in (-1,1):
            aligned_box('Jet bridge',u+sign*12,96,5.5,(14,3.8,3.5),m['concrete'],concourse,.5)
            # Stand paint is flat and above the one apron surface.
            slab('Stand lead-in',strip_polygon([uv(u+sign*20,66),uv(u+sign*20,94)],.45),
                 GROUND+.015,GROUND+.045,m['yellow'],guides)
    tower=clone(assets['tower'],'Building.Tower',uv(-150,124,GROUND),.70)
    tower.parent=env; tower['obstacle_kind']='building'
    for i,(u,v,w,d) in enumerate(((235,128,45,27),(240,181,42,25))):
        service=group('Building.Service.'+str(i),env,'building')
        aligned_box('Service building',u,v,7,(w,d,11),m['concrete'],service,1.2)
        aligned_box('Service roof',u,v,13,(w+2,d+2,1.4),m['roof'],service,.8)
        for du in (-12,0,12):
            aligned_box('Service bay',u+du,v-d/2-.1,6,(7,.2,6),m['glass'],service,.2)
    for i,u in enumerate((-35,5,45,85,125,165)):
        parked=clone(assets['narrowbody'],'Parked.'+str(i+1),uv(u,94),.42,340)
        parked.parent=env; parked['obstacle_kind']='parked_aircraft'
    # Vegetation stays in peripheral landscape pockets, away from the whole
    # movement area and its extended approaches (including canopy radius).
    rng=random.Random(18)
    for j in range(95):
        x,y=rng.uniform(-425,425),rng.uniform(-422,315)
        if -365<x<345 and -210<y<285:continue
        p=Vector((x,y,0))
        clear=False
        for spec in specs.values():
            a=math.radians(spec['heading']); along=Vector((math.sin(a),math.cos(a),0))
            across=Vector((along.y,-along.x,0)); delta=p-Vector((*spec['center'],0))
            if abs(delta.dot(along))<spec['length']/2+115 and abs(delta.dot(across))<42:clear=True
        if clear or (x>-90 and y<-215):continue
        tree=group('Tree.'+str(j),env,'tree'); h=rng.uniform(5,8)
        cylinder('Tree trunk',(x,y,2),.4,2.8,m['concrete'],tree,8)
        sphere('Tree canopy',(x,y,h*.65+1.8),(h*.42,h*.42,h*.58),m['tree' if j%2 else 'tree2'],tree)
    text('North letter','N',(375,285,1.1),10,m['white'],ground)
    slab('North arrow',[(375,274),(369,254),(375,260),(381,254)],1.02,1.08,m['white'],ground)
    return env,specs


def route_ribbon(name, points, width, mat, parent, top=GROUND+.13):
    return slab(name,strip_polygon(points,width),top-.025,top,mat,parent)


def animate_demo(s, assets, specs, m, clone):
    demo=root('Airport.Demonstration',kind='illustrative_animation',forecast_connected=False)
    phases=[('25',True),('07',True),('07',False)]
    planes={}
    for key,asset in [('arrive_north','narrowbody'),('arrive_south','widebody'),
                      ('depart_center','narrowbody'),('depart_flex','narrowbody')]:
        p=clone(assets[asset],'Flight.'+key,scale=.42 if asset=='widebody' else .60)
        p.parent=demo; p['demo_role']=key; planes[key]=p
    records=[]
    for phase,(od,usable) in enumerate(phases):
        start=phase*PHASE_FRAMES+1; end=start+PHASE_FRAMES-1
        routes=routes_for(specs,od,usable)
        timing={key:dict(start=.08,finish=.92) for key in planes}
        timing['arrive_south']=dict(start=.18,finish=.94)
        if not usable:
            timing['depart_center']=dict(start=.02,finish=.46)
            timing['depart_flex']=dict(start=.50,finish=.96)
        records.append(dict(start_frame=start,end_frame=end,od=od,runway_18_usable=usable,
                            paths={k:[list(p) for p in v] for k,v in routes.items()},timing=timing))
        s.timeline_markers.new(f'{phase+1} | OD {od} | 18 '+('OFFEN' if usable else 'GESPERRT'),frame=start)
        for key,p in planes.items():
            points=fillet(routes[key]); last_yaw=None; clock=timing[key]
            for frame in range(start,end+1):
                t=(frame-start)/(PHASE_FRAMES-1)
                progress=max(0,min(1,(t-clock['start'])/(clock['finish']-clock['start'])))
                pos,tangent=sample(points,progress)
                yaw=math.atan2(-tangent.x,tangent.y)
                if last_yaw is not None:
                    while yaw-last_yaw>math.pi:yaw-=math.tau
                    while yaw-last_yaw<-math.pi:yaw+=math.tau
                last_yaw=yaw
                pitch=math.atan2(tangent.z,math.hypot(tangent.x,tangent.y))*min(1,max(0,(pos.z-GROUND)/12))
                p.location=pos; p.rotation_euler=(pitch,0,yaw)
                p.keyframe_insert(data_path='location',frame=frame)
                p.keyframe_insert(data_path='rotation_euler',frame=frame)
        state=root('State.'+str(phase+1),od=od,runway_18_usable=usable)
        state.parent=demo
        # A flat state card remains readable from both the hero and plan views.
        box('State card',(125,-310,1.0),(350,112,.5),m['concrete'],state,5)
        text('State number',f'0{phase+1}  /  03     DEMO',(125,-274,1.32),8,m['navy'],state)
        text('Operating direction','BETRIEBSRICHTUNG  '+od,(125,-294,1.32),12,m['navy'],state)
        text('Runway 18 status','BAHN 18  '+('OFFEN' if usable else 'GESPERRT'),
             (125,-317,1.32),11,m['green' if usable else 'red'],state)
        explanation='ABFLUEGE: MITTELBAHN + 18' if usable else 'ABFLUEGE: NUR MITTELBAHN'
        text('Allocation explanation',explanation,(125,-340,1.32),7.5,m['navy'],state)
        text('Demo provenance','FRA  /  ILLUSTRATIVE BEISPIELWEGE',(125,-357,1.32),4.5,m['navy'],state)
        for key,spec in specs.items():
            heading=180 if key=='west' else (70 if od=='07' else 250)
            a=math.radians(heading); tip=Vector((math.sin(a),math.cos(a),0))
            side=Vector((tip.y,-tip.x,0))
            c=Vector((*spec['center'],1.15))+(Vector((25,0,0)) if key=='west' else V*23)
            color=m['green'] if key=='west' else m['blue']
            if key=='west' and not usable:
                for sign in (-1,1):
                    route_ribbon('Closed cross',[c+Vector((-8,-8*sign,0)),c+Vector((8,8*sign,0))],2.2,m['red'],state,1.2)
                text('Closed label','18 ZU',(c.x+10,c.y-24,1.2),8,m['red'],state)
            else:
                route_ribbon('Direction shaft',[c-tip*18,c+tip*14],1.4,color,state,1.2)
                slab('Direction head',[c+tip*26,c+tip*10+side*5,c+tip*10-side*5],1.17,1.2,color,state)
        # The assigned taxi route has one distinct colour; the closure example
        # visibly follows the same departure runway as the first aircraft.
        route=fillet(routes['depart_flex'][:-2])
        route_ribbon('Assigned departure route',route,1.15,m['green' if usable else 'yellow'],state)
        for f in (1,480,481,960,961,1440):
            active=(f-1)//PHASE_FRAMES==phase
            state.scale=(1,1,1) if active else (0,0,0)
            state.keyframe_insert(data_path='scale',frame=f)
    # Per-frame aircraft samples and stepped state visibility must not ease
    # through the hard cuts between the three independent examples.
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation='CONSTANT' if curve.data_path=='scale' else 'LINEAR'
    s.frame_start=1; s.frame_end=PHASE_FRAMES*3; s.frame_set(240)
    return demo,records
