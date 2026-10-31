"""Build watertight triangulated planar unions in an isolated Shapely runtime.

JSON stdin/stdout keeps Blender independent of Python binary wheel versions.
"""
import json
import sys

from shapely import Polygon, LineString, unary_union, constrained_delaunay_triangles, orient_polygons


def build(data):
    parts=[Polygon(p) for p in data.get('polygons',[])]
    parts += [LineString(p).buffer(data['width']/2,cap_style='flat',join_style='round')
              for p in data.get('paths',[])]
    region=unary_union(parts)
    if data.get('cutouts'):
        region=region.difference(unary_union([Polygon(p) for p in data['cutouts']]))
    assert region.is_valid and not region.is_empty
    region=orient_polygons(region)
    triangles=list(constrained_delaunay_triangles(region).geoms)
    assert abs(sum(t.area for t in triangles)-region.area)<1e-5
    vertices=[]; indices={}
    def index(p):
        key=tuple(p[:2])
        if key not in indices:
            indices[key]=len(vertices); vertices.append(key)
        return indices[key]
    faces=[]
    for triangle in triangles:
        points=list(triangle.exterior.coords)[:3]
        a,b,c=points
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:points.reverse()
        faces.append([index(p) for p in points])
    boundaries=[]
    for poly in ([region] if region.geom_type=='Polygon' else region.geoms):
        for ring in [poly.exterior,*poly.interiors]:
            boundaries.append([index(p) for p in list(ring.coords)[:-1]])
    return dict(vertices=vertices,triangles=faces,boundaries=boundaries,area=region.area)


if __name__=='__main__':
    print(json.dumps(build(json.load(sys.stdin))))
