"""Small modelling helpers and original airport assets. Blender Python only."""
import math
import bpy
from mathutils import Vector


def material(name, color, roughness=.5, metallic=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m


def palette():
    return {
        'ivory': material('Airframe · porcelain', (.82, .85, .83), .27, .22),
        'wing': material('Wing · pearl aluminium', (.60, .66, .67), .32, .35),
        'navy': material('Livery · midnight blue', (.028, .075, .12), .32, .18),
        'glass': material('Glass · smoked blue', (.042, .105, .135), .19, .48),
        'metal': material('Metal · satin titanium', (.30, .37, .39), .3, .78),
        'dark': material('Engine · graphite', (.032, .041, .047), .46, .35),
        'rubber': material('Tyres', (.024, .029, .033), .78),
        'white': material('Marking · warm white', (.91, .91, .83), .75),
        'yellow': material('Marking · taxi yellow', (.87, .59, .13), .62),
        'asphalt': material('Runway · charcoal', (.115, .143, .157), .94),
        'shoulder': material('Shoulder · slate', (.26, .30, .30), .96),
        'concrete': material('Architecture · limestone', (.70, .73, .70), .73),
        'roof': material('Roof · pale zinc', (.47, .56, .56), .58, .22),
        'apron': material('Apron · warm concrete', (.52, .56, .53), .91),
        'grass': material('Landscape · sage', (.34, .46, .34), 1),
        'grass2': material('Landscape · light sage', (.43, .54, .40), 1),
        'tree': material('Trees · eucalyptus', (.19, .34, .24), .98),
        'tree2': material('Trees · olive', (.27, .40, .26), .98),
        'base': material('Diorama · edge', (.53, .62, .54), .83),
        'paper': material('Studio · chalk', (.80, .83, .80), .94),
        'blue': material('Flow · blue', (.035, .32, .57), .45, emission=.2),
        'green': material('Flow · teal', (.035, .48, .32), .45, emission=.2),
        'red': material('Status · coral', (.72, .13, .075), .45, emission=.2),
        'light': material('Lights · warm', (1, .85, .55), .3, emission=3),
    }


def root(name, **props):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.empty_display_type = 'PLAIN_AXES'
    o.empty_display_size = 2
    for k, v in props.items():
        o[k] = v
    return o


def finish(o, name, mat=None, parent=None, smooth=False):
    o.name = name
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    if smooth and o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def mesh(name, verts, faces, mat, parent=None, smooth=False):
    d = bpy.data.meshes.new(name)
    d.from_pydata(verts, [], faces)
    d.update()
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    return finish(o, name, mat, parent, smooth)


def bevel(o, width, segments=3):
    b = o.modifiers.new('Edge highlights', 'BEVEL')
    b.width, b.segments = width, segments
    b = o.modifiers.new('Corner normals', 'WEIGHTED_NORMAL')
    b.keep_sharp = True
    return o


def box(name, loc, dims, mat, parent=None, edge=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(o, name, mat, parent)
    if edge:
        bevel(o, edge)
    return o


def cylinder(name, loc, radius, depth, mat, parent=None, vertices=32, axis='Z'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    if axis == 'X':
        o.rotation_euler.y = math.pi / 2
    elif axis == 'Y':
        o.rotation_euler.x = math.pi / 2
    finish(o, name, mat, parent, True)
    return o


def sphere(name, loc, scale, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc)
    o = bpy.context.object
    o.scale = scale
    return finish(o, name, mat, parent, True)


def beam(name, a, b, radius, mat, parent=None, vertices=12):
    a, b = Vector(a), Vector(b)
    o = cylinder(name, (a+b)/2, radius, (b-a).length, mat, parent, vertices)
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return o


def line(name, points, radius, mat, parent=None):
    c = bpy.data.curves.new(name, 'CURVE')
    c.dimensions = '3D'
    c.bevel_depth, c.bevel_resolution = radius, 2
    s = c.splines.new('POLY')
    s.points.add(len(points)-1)
    for p, co in zip(s.points, points):
        p.co = (*co, 1)
    o = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(o)
    return finish(o, name, mat, parent)


def pavement(name, points, width, mat, parent=None):
    for a,b in zip(points,points[1:]):
        a,b=Vector(a),Vector(b)
        side=Vector((b.y-a.y,a.x-b.x,0)).normalized()*width/2
        mesh(name,[a-side,a+side,b+side,b-side],[(0,1,2,3)],mat,parent)
    for point in points[1:-1]:
        cylinder(name+' corner',point,width/2,.04,mat,parent,24)


def text(name, body, loc, size, mat, parent=None, rotation=0):
    c = bpy.data.curves.new(name, 'FONT')
    c.body, c.size, c.align_x, c.align_y = body, size, 'CENTER', 'CENTER'
    c.extrude = .002
    o = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(o)
    o.location, o.rotation_euler.z = loc, rotation
    return finish(o, name, mat, parent)


def loft_y(name, profile, mat, parent, sides=64):
    """Profile tuples: longitudinal y, radius x, radius z, center z."""
    v = [(rx*math.sin(a*2*math.pi/sides), y, z+rz*math.cos(a*2*math.pi/sides))
         for y, rx, rz, z in profile for a in range(sides)]
    f = []
    for j in range(len(profile)-1):
        for i in range(sides):
            a, b = j*sides+i, j*sides+(i+1)%sides
            f.append((a, b, b+sides, a+sides))
    f.extend([tuple(reversed(range(sides))), tuple((len(profile)-1)*sides+i for i in range(sides))])
    return mesh(name, v, f, mat, parent, True)


def wing(name, stations, mat, parent, sign=1):
    # Closed airfoil sections: span, leading y, chord, height, thickness.
    v = []
    n = 24
    for x, y, chord, z, thick in stations:
        for j in range(n):
            a = 2*math.pi*j/n
            t = (1-math.cos(a))/2
            v.append((sign*x, y-chord*t, z+thick*math.sin(a)*(.85-.4*t)))
    f = []
    for s in range(len(stations)-1):
        for j in range(n):
            a, b = s*n+j, s*n+(j+1)%n
            f.append((a, b, b+n, a+n))
    f += [tuple(reversed(range(n))), tuple((len(stations)-1)*n+j for j in range(n))]
    return mesh(name, v, f, mat, parent, True)


def extruded_polygon(name, points, thickness, mat, parent, axis='X'):
    v=[]
    for offset in (-thickness/2, thickness/2):
        for a,b in points:
            v.append((offset,a,b) if axis == 'X' else (a,b,offset))
    n=len(points)
    f=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return bevel(mesh(name,v,f,mat,parent), min(thickness*.25,.09),2)


def aircraft(name, m, wide=False):
    """Generic original twinjets; +Y nose, Z up, origin at ground center."""
    r = root(name, kind='aircraft', forward='+Y', units='metres', generic=True)
    length, radius, span = (64, 3.0, 61) if wide else (37.6, 1.95, 35.8)
    h = 6.0 if wide else 4.1
    k = length/37.6
    profile = [(-.50,.02,.10),(-.48,.22,.17),(-.44,.52,.11),(-.39,.79,.05),
               (-.33,.96,.01),(-.25,1,0),(-.1,1,0),(.06,1,0),(.23,1,0),
               (.32,.97,0),(.37,.87,-.01),(.41,.69,-.06),(.45,.43,-.13),
               (.48,.20,-.18),(.499,.025,-.20)]
    loft_y('Fuselage',[(y*length,rx*radius,rx*radius,h+dz*radius) for y,rx,dz in profile],m['ivory'],r)
    wing_stations=[(.6,3.9*k,8.0*k,h-.8),(.18*span,1.6*k,5.9*k,h-.45),
                   (.39*span,-3.6*k,2.5*k,h+.5),(.5*span,-5.8*k,1.15*k,h+1.25)]
    for s in (-1,1):
        wing('Wing.L' if s<0 else 'Wing.R',[(x,y,c,z,.20*k*(1-x/span)) for x,y,c,z in wing_stations],m['wing'],r,s)
        tip=wing_stations[-1]
        wing('Winglet',[(tip[0],tip[1],tip[2],tip[3],.10*k),
                        (tip[0]+.6*k,tip[1]-.5*k,.65*k,tip[3]+1.7*k,.06*k)],m['navy'],r,s)
        wing('Horizontal stabilizer',[(.6,-12.2*k,4.5*k,h+.6,.18*k),
             (6.2*k,-15.4*k,1.2*k,h+1.4,.08*k)],m['wing'],r,s)
        # Flap seams and track fairings make close-up geometry legible.
        line('Flap seam',[(s*x,y-c*.73,z+.14*k) for x,y,c,z in wing_stations[:-1]],.018*k,m['metal'],r)
        for x,y,c,z in wing_stations[1:3]:
            sphere('Flap track',(s*x,y-c+.15*k,z-.23*k),(.18*k,1.35*k,.20*k),m['ivory'],r)
        ex,ey,ez=s*5.65*k,1.35*k,h-1.65*k
        er=1.12*k
        p=[(-2.1,.64),(-1.8,.84),(-1.0,1.0),(.9,1.02),(1.65,1),
           (1.82,.93),(1.77,.82),(1.30,.80),(.65,.75)]
        eng=loft_y('Nacelle',[(ey+y*k, rr*er,rr*er,ez) for y,rr in p],m['ivory'],r,48)
        eng.location.x=ex
        # Real open intake with recessed fan, rim and exhaust.
        for poly in eng.data.polygons:
            if poly.index>=4*48:
                if len(eng.data.materials)<2: eng.data.materials.append(m['metal'])
                poly.material_index=1
        cylinder('Intake shadow',(ex,ey+.91*k,ez),.85*er,.06*k,m['dark'],r,48,'Y')
        for j in range(20):
            a=j*math.tau/20
            coords=[]
            for rad,ang,yy in [(.22,a,.99),(.80,a+.11,.94),(.82,a+.23,.98),(.28,a+.20,1.04)]:
                coords.append((ex+er*rad*math.cos(ang),ey+yy*k,ez+er*rad*math.sin(ang)))
            mesh('Fan blade',coords,[(0,1,2,3)],m['metal'],r)
        sphere('Fan spinner',(ex,ey+1.03*k,ez),(.29*k,.41*k,.29*k),m['metal'],r)
        cylinder('Exhaust',(ex,ey-2.12*k,ez),.56*er,.13*k,m['dark'],r,40,'Y')
        box('Pylon',(ex,ey-.6*k,ez+.9*k),(.35*k,2.5*k,.7*k),m['wing'],r,.14*k)
        # Individual cabin apertures are rounded and flush with the skin.
        window_count=42 if wide else 29
        for j in range(window_count):
            y=-length*.29+j*(length*.60/(window_count-1))
            x=s*radius*.973
            o=box('Cabin window',(x,y,h+radius*.24),(.035,.31*k,.39*k),m['glass'],r,.10*k)
        for y in (-length*.32, length*.29):
            # Quiet door outlines, with a pale interior and small handle.
            x=s*radius*.954
            box('Door reveal',(x,y,h+.10*k),(.055,.90*k,1.55*k),m['metal'],r,.12*k)
            box('Door leaf',(x+s*.035,y,h+.10*k),(.035,.81*k,1.43*k),m['ivory'],r,.10*k)
            box('Door window',(x+s*.06,y,h+.53*k),(.035,.24*k,.29*k),m['glass'],r,.07*k)
        # Cockpit glazing follows the taper with separate windshield panes.
        for a0,a1 in ((32,58),(61,82),(85,105)):
            verts=[];faces=[]
            for row in range(7):
                yy=.390+row/6*.047
                for lo,hi in zip(profile,profile[1:]):
                    if lo[0]<=yy<=hi[0]:
                        t=(yy-lo[0])/(hi[0]-lo[0])
                        rr=lo[1]+(hi[1]-lo[1])*t
                        zc=lo[2]+(hi[2]-lo[2])*t
                        break
                for col in range(7):
                    a=math.radians(a0+(a1-a0)*col/6)*s
                    verts.append(((radius*rr+.025)*math.sin(a),length*yy,
                                  h+zc*radius+(radius*rr+.025)*math.cos(a)))
            for row in range(6):
                for col in range(6):
                    q=row*7+col;faces.append((q,q+1,q+8,q+7))
            mesh('Cockpit pane',verts,faces,m['glass'],r,True)
        lightmat=m['red'] if s<0 else m['green']
        sphere('Wing navigation light',(s*span*.5,-5.8*k,h+1.28),(.11*k,.15*k,.09*k),lightmat,r)
    fin=extruded_polygon('Vertical stabilizer',[(-13.4*k,h+.6),(-15.7*k,h+7.3*k),
          (-18.1*k,h+7.5*k),(-17.7*k,h+.55)],.34*k,m['navy'],r)
    # Light inset on the tail avoids an airline-specific livery.
    for s in (-1,1):
        mesh('Tail inset',[(s*.18*k,-15.9*k,h+5.9*k),(s*.18*k,-17.4*k,h+6.15*k),
             (s*.18*k,-17.3*k,h+5.5*k),(s*.18*k,-16.1*k,h+5.25*k)],[(0,1,2,3)],m['ivory'],r)
    for label,x,y in [('Nose',0,length*.34),('Left',-2.65*k,-2.8*k),('Right',2.65*k,-2.8*k)]:
        g=root('Gear.'+label, role='retractable landing gear')
        g.parent=r
        g.location=(x,y,h-radius*.7)
        ground=h-radius*.7
        wr=.43*k if label=='Nose' else .57*k
        beam('Oleo',(0,0,0),(0,0,-ground+wr),.12*k,m['metal'],g)
        beam('Gear brace',(0,.65*k,-.2*k),(0,0,-ground+wr+.25*k),.075*k,m['metal'],g)
        for xx in (-.29*k,.29*k):
            wheel=cylinder('Tyre',(xx,0,-ground+wr),wr,.27*k,m['rubber'],g,32,'X')
            bevel(wheel,.08*k,3)
            cylinder('Wheel hub',(xx+math.copysign(.145*k,xx),0,-ground+wr),wr*.53,.035*k,m['metal'],g,24,'X')
        if wide and label!='Nose':
            for yy in (-.8,.8):
                for xx in (-.29*k,.29*k):
                    wheel=cylinder('Bogie tyre',(xx,yy*k,-ground+wr),wr,.27*k,m['rubber'],g,32,'X')
                    bevel(wheel,.08*k,3)
    r['length_m'],r['span_m']=length,span
    return r


def tower(m):
    r=root('Tower',kind='control_tower',units='metres',inspired_by='DFS Frankfurt; simplified original geometry')
    box('Foundation',(0,0,.6),(20,18,1.2),m['concrete'],r,1)
    box('Lower service building',(0,1,3.2),(19,14,5.2),m['concrete'],r,.4)
    box('Service roof',(0,1,6),(20,15,.7),m['roof'],r,.3)
    box('Shaft',(0,0,30),(7.8,7.8,51),m['concrete'],r,.6)
    box('Service spine',(3.9,0,29),(1.4,4.1,49),m['roof'],r,.2)
    for z in range(10,53,5):
        box('Shaft slit',(0,-3.94,z),(.65,.12,1.6),m['glass'],r,.12)
    # Exterior switchback stair on the west face, like the Frankfurt landmark.
    for j in range(12):
        z=6+j*3.8
        y0,y1=(-4,4) if j%2==0 else (4,-4)
        for i in range(19):
            t=i/18
            box('Stair tread',(-5.3,y0+(y1-y0)*t,z+3.8*t),(2.5,.49,.15),m['metal'],r,.03)
        box('Stair landing',(-5.3,y1,z+3.8),(2.8,2,.24),m['concrete'],r,.08)
        for x in (-6.65,-4):
            beam('Stair handrail',(x,y0,z+1),(x,y1,z+4.8),.045,m['metal'],r)
            for i in range(6):
                t=i/5
                yy=y0+(y1-y0)*t
                zz=z+3.8*t
                beam('Stair baluster',(x,yy,zz),(x,yy,zz+1),.035,m['metal'],r)
    for x in (-5.8,5.8):
        for y in (-5.8,5.8):
            beam('Cab support',(x*.5,y*.5,48),(x,y,57),.42,m['concrete'],r,16)
    box('Cab lower deck',(0,0,55.4),(18,15,2.2),m['concrete'],r,.5)
    box('Cab shadow reveal',(0,0,56.8),(17.6,14.6,.6),m['dark'],r,.2)
    # Octagonal glazed cab with a subtly flared window band.
    perimeter=[(-7,-7),(7,-7),(9,-5),(9,5),(7,7),(-7,7),(-9,5),(-9,-5)]
    for i,(x,y) in enumerate(perimeter):
        nx,ny=perimeter[(i+1)%8]
        mesh('Cab glazing',[(x,y,57),(nx,ny,57),(nx*1.08,ny*1.08,62.3),(x*1.08,y*1.08,62.3)],[(0,1,2,3)],m['glass'],r)
        beam('Cab mullion',(x,y,57),(x*1.08,y*1.08,62.5),.13,m['concrete'],r)
        for t in (.33,.67):
            xx,yy=x+(nx-x)*t,y+(ny-y)*t
            beam('Window mullion',(xx,yy,57),(xx*1.08,yy*1.08,62.5),.055,m['metal'],r)
    box('Cab roof',(0,0,62.7),(21,17.5,1),m['concrete'],r,.65)
    box('Roof inset',(0,0,63.4),(16,13,.5),m['roof'],r,.2)
    for x,y,height in [(-5,-3,5),(5,2,6.6),(2,-3,3.5)]:
        beam('Antenna',(x,y,63.5),(x,y,63.5+height),.085,m['metal'],r)
        sphere('Antenna beacon',(x,y,63.5+height),(.15,.15,.19),m['red'],r)
    cylinder('Radar mount',(-2,1,64),.5,2,m['metal'],r)
    radar=root('Radar',role='rotate around local Z')
    radar.parent=r
    radar.location=(-2,1,65.3)
    box('Radar bar',(0,0,0),(6,.65,.65),m['ivory'],radar,.2)
    for x in (-5,0,5):
        box('Service glazing',(x,-6.06,3),(3.5,.08,2.3),m['glass'],r,.1)
    return r


def runway(name, m, length=4000, width=60, labels=('07C','25C'), heading=70):
    r=root(name,kind='runway',units='metres',length_m=length,width_m=width,
           heading_deg=heading,departure_only=(heading==180))
    box('Shoulders',(0,0,-.1),(width+15,length+20,.6),m['shoulder'],r,.25)
    box('Pavement',(0,0,.15),(width,length,.4),m['asphalt'],r,.15)
    markings=root('Markings'); markings.parent=r
    for side in (-1,1):
        box('Edge stripe',(side*(width/2-1.2),0,.38),(.9,length-8,.025),m['white'],markings)
    for y in range(-int(length/2)+300,int(length/2)-300,60):
        box('Centerline',(0,y,.39),(.9,30,.03),m['white'],markings)
    for end,label in enumerate(labels):
        if not label: continue
        sign=-1 if end==0 else 1
        endy=sign*(length/2-42)
        for j in range(6):
            x=3+j*3.2
            for side in (-1,1):
                box('Threshold piano key',(side*x,endy,.39),(1.8,30,.03),m['white'],markings)
        text('Designator.'+label,label,(0,sign*(length/2-125),.41),25,m['white'],markings,0 if sign<0 else math.pi)
        for dist in (300,450,600):
            for side in (-1,1):
                box('Touchdown marking',(side*width*.27,sign*(length/2-dist),.39),
                    (5 if dist==300 else 2.5,35 if dist==300 else 22,.03),m['white'],markings)
        anchor=root('Threshold.'+label,heading_deg=heading if end==0 else (heading+180)%360)
        anchor.parent=r;anchor.location=(0,sign*length/2,.4)
    lights=root('EdgeLights');lights.parent=r
    for y in range(-int(length/2)+20,int(length/2),80):
        for s in (-1,1):
            cylinder('Edge lamp',(s*(width/2+1.5),y,.6),.45,.65,m['light'],lights,8)
    return r
