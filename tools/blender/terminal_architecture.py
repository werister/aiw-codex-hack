"""Landmark Frankfurt-style terminal, authored for the compressed demo layout."""

import math

from geometry import root, box, mesh, line


def _group(name, parent):
    part = root(name)
    part.parent = parent
    return part


def _aligned_box(name, u, v, z, dims, mat, parent, uv, edge=0):
    part = box(name, uv(u, v, z), dims, mat, parent, edge)
    part.rotation_euler.z = math.radians(20)
    return part


def _roof_height(v, center, half_width, edge_z, crown):
    across = (v - center) / half_width
    return edge_z + crown * max(0.0, 1.0 - across * across)


def _curved_roof(name, u0, u1, v_center, half_width, edge_z, crown,
                 thickness, mat, parent, uv, u_steps=18, v_steps=12):
    """Create a capped, shallow vaulted roof.  Coordinates remain in airport UV."""
    upper = []
    lower = []
    for i in range(u_steps + 1):
        u = u0 + (u1 - u0) * i / u_steps
        for j in range(v_steps + 1):
            v = v_center - half_width + 2 * half_width * j / v_steps
            x, y, _ = uv(u, v, 0)
            z = _roof_height(v, v_center, half_width, edge_z, crown)
            upper.append((x, y, z))
            lower.append((x, y, z - thickness))

    row = v_steps + 1
    n = len(upper)
    faces = []
    for i in range(u_steps):
        for j in range(v_steps):
            a = i * row + j
            b = a + row
            faces.append((a, b, b + 1, a + 1))
            faces.append(tuple(reversed((a + n, b + n, b + 1 + n, a + 1 + n))))
    # Close both ends and the long eaves; all faces have real thickness.
    for i in range(u_steps):
        a, b = i * row, (i + 1) * row
        faces.append((a, a + n, b + n, b))
        a, b = i * row + v_steps, (i + 1) * row + v_steps
        faces.append((a, b, b + n, a + n))
    for j in range(v_steps):
        a, b = j, j + 1
        faces.append((a, b, b + n, a + n))
        a, b = u_steps * row + j, u_steps * row + j + 1
        faces.append((a, a + n, b + n, b))
    return mesh(name, upper + lower, faces, mat, parent)


def _concourse_roof(name, center_u, v0, v1, half_width, edge_z, crown,
                    thickness, mat, parent, uv):
    """Vault a narrow pier roof across u, along the terminal-to-gate axis."""
    longitudinal_steps, cross_steps = 12, 8
    upper, lower = [], []
    for i in range(longitudinal_steps + 1):
        v = v0 + (v1 - v0) * i / longitudinal_steps
        for j in range(cross_steps + 1):
            u = center_u - half_width + 2 * half_width * j / cross_steps
            x, y, _ = uv(u, v, 0)
            z = _roof_height(u, center_u, half_width, edge_z, crown)
            upper.append((x, y, z))
            lower.append((x, y, z - thickness))

    row = cross_steps + 1
    n = len(upper)
    faces = []
    for i in range(longitudinal_steps):
        for j in range(cross_steps):
            a, b = i * row + j, i * row + j + 1
            c, d = (i + 1) * row + j + 1, (i + 1) * row + j
            faces.append((a, b, c, d))
            faces.append(tuple(reversed((a + n, b + n, c + n, d + n))))
    # End caps and eaves.
    for i in range(longitudinal_steps):
        a, b = i * row, (i + 1) * row
        faces.append((a, b, b + n, a + n))
        a, b = i * row + cross_steps, (i + 1) * row + cross_steps
        faces.append((a, a + n, b + n, b))
    for j in range(cross_steps):
        a, b = j, j + 1
        faces.append((a, a + n, b + n, b))
        a, b = longitudinal_steps * row + j, longitudinal_steps * row + j + 1
        faces.append((a, b, b + n, a + n))
    return mesh(name, upper + lower, faces, mat, parent)


def _facade_bays(name, u0, u1, v_face, z_base, z_top, parent, m, uv,
                 pitch=4.0):
    """Recessed glazing panels between limestone piers and paired mullions."""
    glass_bottom = z_base + 2.1
    glass_top = z_top - 1.45
    glass_height = glass_top - glass_bottom
    center_z = (glass_top + glass_bottom) / 2
    u = u0 + pitch * 0.52
    bay = 0
    while u < u1 - pitch * 0.45:
        half = pitch * 0.43
        _aligned_box(f'{name} recessed glazing {bay + 1}', u, v_face,
                     center_z, (half * 2, .18, glass_height),
                     m['glass'], parent, uv, .08)
        # Two fine uprights and one shadow reveal articulate each glazed bay.
        for du in (-half, half):
            _aligned_box(f'{name} curtain mullion', u + du, v_face - .13,
                         center_z, (.11, .12, glass_height + .16),
                         m['metal'], parent, uv, .035)
        _aligned_box(f'{name} recessed sill', u, v_face - .045,
                     glass_bottom - .12, (half * 1.95, .2, .16),
                     m['roof'], parent, uv, .035)
        bay += 1
        u += pitch


def _roof_ribs(name, u0, u1, v_center, half_width, edge_z, crown,
               parent, uv, material, spacing=12):
    for u in range(math.ceil(u0 / spacing) * spacing, int(u1), spacing):
        points = []
        for j in range(9):
            v = v_center - half_width + 2 * half_width * j / 8
            x, y, _ = uv(u, v, 0)
            points.append((x, y, _roof_height(v, v_center, half_width, edge_z, crown) + .045))
        line(name, points, .14, material, parent)


def build_terminal(m, env, uv):
    """Build the detailed terminal and three concourses inside reserved bounds.

    Roof/facade footprint stays within u[-57,187], v[118,146.5]. The three
    concourses stay within u[-22,152], v[78,124], leaving the runways clear.
    """
    terminal = root('Building.Terminal', obstacle_kind='building', landmark='Frankfurt terminal')
    terminal.parent = env

    # A single deeply layered plinth makes the hall read as a real building,
    # while the roof silhouette steps up towards the central glazed volume.
    _aligned_box('Terminal stone podium', 65, 132.2, 3.12,
                 (242, 28.2, 2.95), m['concrete'], terminal, uv, 1.2)
    _aligned_box('Terminal recessed base', 65, 132.2, 4.8,
                 (238, 24.0, .55), m['roof'], terminal, uv, .25)

    halls = [
        dict(name='West hall', u0=-55, u1=-1, center=-28, floor=5.05,
             top=14.25, roof_edge=15.1, crown=.52),
        dict(name='Central hall', u0=5, u1=125, center=65, floor=5.05,
             top=17.2, roof_edge=18.25, crown=1.72),
        dict(name='East hall', u0=133, u1=183, center=158, floor=5.05,
             top=15.4, roof_edge=16.2, crown=.72),
    ]
    for index, hall in enumerate(halls):
        part = _group('Terminal hall volume ' + str(index + 1), terminal)
        length = hall['u1'] - hall['u0']
        height = hall['top'] - hall['floor']
        _aligned_box(hall['name'] + ' limestone shell', hall['center'], 132.2,
                     hall['floor'] + height / 2, (length, 23.5, height),
                     m['concrete'], part, uv, .35)
        # Recessed glass bands on the landside and apron side.
        for side in (-1, 1):
            face_v = 132.2 + side * 11.79
            _facade_bays(hall['name'], hall['u0'] + 2.0, hall['u1'] - 2.0,
                         face_v, hall['floor'], hall['top'], part, m, uv)
            _aligned_box(hall['name'] + ' horizontal spandrel', hall['center'],
                         face_v - side * .09, hall['floor'] + 1.18,
                         (length - 1.0, .3, .46), m['roof'], part, uv, .08)
            _aligned_box(hall['name'] + ' upper lintel', hall['center'],
                         face_v - side * .08, hall['top'] - .38,
                         (length - 1.0, .34, .6), m['concrete'], part, uv, .08)
        # Solid ends, the shadow line at the eaves, and a proper stepped roof.
        for u in (hall['u0'] + .95, hall['u1'] - .95):
            _aligned_box(hall['name'] + ' end pier', u, 132.2,
                         hall['floor'] + height / 2,
                         (1.9, 24.2, height + .12), m['concrete'], part, uv, .14)
        _curved_roof(hall['name'] + ' vaulted roof', hall['u0'] - .35,
                     hall['u1'] + .35, 132.2, 14.05,
                     hall['roof_edge'], hall['crown'], .8,
                     m['roof'], part, uv)
        _roof_ribs(hall['name'] + ' canopy rib', hall['u0'] + 4,
                   hall['u1'] - 2, 132.2, 14.05, hall['roof_edge'],
                   hall['crown'], part, uv, m['metal'], 12)

        # A narrow glazed clerestory catches light along the crown of each roof.
        skylight_v = 132.2
        skylight_z = hall['roof_edge'] + hall['crown'] + .08
        _aligned_box(hall['name'] + ' clerestory glass', hall['center'],
                     skylight_v, skylight_z, (length - 8, 2.35, .09),
                     m['glass'], part, uv, .12)
        for du in range(int(hall['u0']) + 8, int(hall['u1']) - 5, 8):
            _aligned_box(hall['name'] + ' clerestory frame', du, skylight_v,
                         skylight_z + .08, (.12, 2.55, .12),
                         m['metal'], part, uv, .035)

    # Glass links close the 6–8 m gaps between the stepped halls. Their roof
    # lines sit below both neighboring canopies, leaving the skyline legible.
    for name, center_u, length in (('West link', 2, 8), ('East link', 129, 10)):
        link = _group('Terminal glazed ' + name, terminal)
        _aligned_box(name + ' volume', center_u, 132.2, 9.1,
                     (length, 21.8, 8.1), m['glass'], link, uv, .2)
        _aligned_box(name + ' canopy', center_u, 132.2, 13.55,
                     (length + 1.4, 25.2, .55), m['roof'], link, uv, .22)
        for side in (-1, 1):
            for u in range(int(center_u - length / 2) + 2,
                           int(center_u + length / 2), 2):
                _aligned_box(name + ' link mullion', u, 132.2 + side * 11.02,
                             9.25, (.09, .14, 7.7), m['metal'], link, uv, .025)

    # Continuous sheltered curb-side canopy with fine supports and a dark
    # recessed soffit. It sits on the terminal side of the apron facade.
    canopy = _group('Terminal entrance canopy', terminal)
    _aligned_box('Terminal canopy soffit', 65, 117.65, 7.0,
                 (205, 4.3, .34), m['roof'], canopy, uv, .18)
    _aligned_box('Terminal canopy fascia', 65, 115.55, 7.0,
                 (205, .36, .64), m['concrete'], canopy, uv, .12)
    for u in range(-31, 163, 16):
        _aligned_box('Canopy bracket', u, 118.65, 6.0,
                     (.28, 2.1, 2.1), m['metal'], canopy, uv, .08)

    # Three individually vaulted gate piers, with larger central glazing,
    # polished roof caps, continuous window bands and subtle service doors.
    for index, center_u in enumerate((-15, 65, 145)):
        pier = root('Building.Concourse.' + str(index + 1),
                    obstacle_kind='building', role='passenger_concourse')
        pier.parent = env
        _aligned_box('Concourse limestone pier', center_u, 101, 8.25,
                     (12, 42, 12.8), m['concrete'], pier, uv, .55)
        _aligned_box('Concourse apron-side glass', center_u, 80.0, 9.1,
                     (10.7, .18, 7.1), m['glass'], pier, uv, .07)
        _aligned_box('Concourse landside glass', center_u, 122.0, 9.1,
                     (10.7, .18, 7.1), m['glass'], pier, uv, .07)
        for du in (-4.1, 0, 4.1):
            _aligned_box('Concourse mullion', center_u + du, 79.83, 9.1,
                         (.16, .14, 7.35), m['metal'], pier, uv, .04)
            _aligned_box('Concourse mullion', center_u + du, 122.17, 9.1,
                         (.16, .14, 7.35), m['metal'], pier, uv, .04)
        _aligned_box('Concourse roof fascia', center_u, 101, 15.72,
                     (14.2, 45.8, .62), m['concrete'], pier, uv, .24)
        _concourse_roof('Concourse vaulted roof', center_u, 78, 124,
                        7.0, 16.03, .60, .54, m['roof'], pier, uv)
        # Low raised glazing strips repeat on the gate roof; metal caps sit on
        # the surface with a small deliberate separation from the zinc skin.
        for offset_u in (-2.5, 2.5):
            _aligned_box('Concourse rooflight', center_u + offset_u, 101,
                         16.69, (1.45, 34, .12), m['glass'], pier, uv, .08)
        # Pair of articulated bridges meets the stands at the outer edge.
        for sign in (-1, 1):
            bridge_u = center_u + sign * 12
            bridge = _group('Jet bridge ' + str(index + 1) + '.' + str(sign), pier)
            _aligned_box('Jet bridge enclosure', bridge_u, 96, 3.85,
                         (14, 3.8, 1.7), m['concrete'], bridge, uv, .25)
            _aligned_box('Jet bridge glazing', bridge_u, 94.02, 3.9,
                         (11.8, .12, 1.0), m['glass'], bridge, uv, .07)
            _aligned_box('Jet bridge roof', bridge_u, 96, 4.78,
                         (13.2, 3.55, .18), m['roof'], bridge, uv, .08)
            for offset_u in (-5.6, 5.6):
                _aligned_box('Bridge support', bridge_u + offset_u, 96, 2.45,
                             (.36, .42, 1.1), m['metal'], bridge, uv, .07)
                _aligned_box('Bridge support shoe', bridge_u + offset_u, 96, 1.98,
                             (.68, .64, .18), m['concrete'], bridge, uv, .07)

    return terminal
