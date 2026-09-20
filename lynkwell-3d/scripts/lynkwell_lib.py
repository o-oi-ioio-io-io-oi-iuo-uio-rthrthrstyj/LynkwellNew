"""Lynkwell Digital - shared brand + build helpers for all 3D assets."""
import bpy, bmesh, math
from mathutils import Vector

ROOT = "/Users/jackdworkin/Claude Code Projects/lynkwell-3d"

# ---------------------------------------------------------------- brand
HEX = {
    "bg":       "F2EFE8",   # bone / cream background
    "cream":    "E4DFD4",   # primary surface
    "stone":    "B8B2A7",   # mid tone
    "charcoal": "1A1A1A",   # dark
    "cobalt":   "2B4BFF",   # accent
}

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hexlin(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def _sock(bsdf, *names):
    for n in names:
        if n in bsdf.inputs:
            return bsdf.inputs[n]
    return None

def make_material(name, hex_color, roughness, metallic=0.0,
                  emission_hex=None, emission_strength=0.0):
    """Principled BSDF only - glTF safe (base color / metallic / roughness / emission)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = hexlin(hex_color)
    _sock(bsdf, "Base Color").default_value = (*col, 1.0)
    _sock(bsdf, "Metallic").default_value = metallic
    _sock(bsdf, "Roughness").default_value = roughness
    es = _sock(bsdf, "Emission Strength")
    ec = _sock(bsdf, "Emission Color", "Emission")
    if emission_hex:
        ec.default_value = (*hexlin(emission_hex), 1.0)
        es.default_value = emission_strength
    else:
        es.default_value = 0.0
    mat.diffuse_color = (*col, 1.0)
    mat.roughness = roughness
    mat.metallic = metallic
    return mat

def brand_materials():
    return {
        "mat_cream":       make_material("mat_cream",    HEX["cream"],    0.60),
        "mat_stone":       make_material("mat_stone",    HEX["stone"],    0.50),
        "mat_charcoal":    make_material("mat_charcoal", HEX["charcoal"], 0.35),
        "mat_cobalt":      make_material("mat_cobalt",   HEX["cobalt"],   0.15),
        "mat_cobalt_glow": make_material("mat_cobalt_glow", HEX["cobalt"], 0.15,
                                         emission_hex=HEX["cobalt"], emission_strength=1.0),
    }

# ---------------------------------------------------------------- scene
def reset_scene():
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.render.fps = 24
    return sc

def get_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def new_object(name, mesh, collection, material=None):
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    if material is not None:
        ob.data.materials.append(material)
    return ob

# ---------------------------------------------------------------- meshes
def mesh_from_bm(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me

def chain_link_mesh(name, a, e, r, n_semi=12, n_straight=4, n_ring=14):
    """Stadium-path tube ('chain link') centred on the origin, long axis = +X, flat in XY.

    a  = radius of the two end semicircles (centreline)
    e  = length of the straight sections (centreline)
    r  = tube radius
    Outer size: length = e + 2a + 2r , width = 2a + 2r
    """
    pts = []
    for k in range(n_semi):                       # right cap, -90 -> +90
        t = math.radians(-90.0 + 180.0 * k / n_semi)
        pts.append(Vector((e / 2 + a * math.cos(t), a * math.sin(t), 0.0)))
    for k in range(n_straight):                   # top run, +X -> -X
        s = k / n_straight
        pts.append(Vector((e / 2 - e * s, a, 0.0)))
    for k in range(n_semi):                       # left cap, +90 -> +270
        t = math.radians(90.0 + 180.0 * k / n_semi)
        pts.append(Vector((-e / 2 + a * math.cos(t), a * math.sin(t), 0.0)))
    for k in range(n_straight):                   # bottom run, -X -> +X
        s = k / n_straight
        pts.append(Vector((-e / 2 + e * s, -a, 0.0)))

    n = len(pts)
    bm = bmesh.new()
    rings = []
    up = Vector((0.0, 0.0, 1.0))
    for i, p in enumerate(pts):
        tan = (pts[(i + 1) % n] - pts[(i - 1) % n]).normalized()
        side = tan.cross(up).normalized()
        ring = []
        for j in range(n_ring):
            ph = 2.0 * math.pi * j / n_ring
            ring.append(bm.verts.new(p + r * (math.cos(ph) * side + math.sin(ph) * up)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for i in range(n):
        ra, rb = rings[i], rings[(i + 1) % n]
        for j in range(n_ring):
            j2 = (j + 1) % n_ring
            f = bm.faces.new((ra[j], rb[j], rb[j2], ra[j2]))
            f.smooth = True
    return mesh_from_bm(bm, name)

def sphere_mesh(name, radius, u=28, v=14):
    bm = bmesh.new()
    try:
        bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=radius)
    except TypeError:
        bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, diameter=radius)
    for f in bm.faces:
        f.smooth = True
    return mesh_from_bm(bm, name)

def rod_mesh(name, radius, length, segments=12):
    """Cylinder along +Z, centred. Round sides smooth, flat caps."""
    bm = bmesh.new()
    try:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              radius1=radius, radius2=radius, depth=length)
    except TypeError:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              diameter1=radius * 2, diameter2=radius * 2, depth=length)
    for f in bm.faces:
        f.smooth = abs(f.normal.z) < 0.9
    return mesh_from_bm(bm, name)

def add_bevel(ob, width=0.0035, segments=2, angle_deg=30.0):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle_deg)
    m.miter_outer = "MITER_ARC"
    return m

# ---------------------------------------------------------------- stats
def tri_count(objects):
    dg = bpy.context.evaluated_depsgraph_get()
    total, per = 0, {}
    for ob in objects:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        ev.to_mesh_clear()
        per[ob.name] = n
        total += n
    return total, per

def recentre(objects):
    """Shift every object so the group's world bounding-box centre sits at the origin."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in objects:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(dg)
        mw = ob.matrix_world
        for c in ev.bound_box:
            w = mw @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    mid = (lo + hi) * 0.5
    for ob in objects:
        ob.location = ob.location - mid
    bpy.context.view_layer.update()
    return mid, (hi - lo)

# ---------------------------------------------------------------- base pose
# Animation runs must never read the live transform: if a previous run left an
# action bound, Blender writes the evaluated (animated) value back onto the
# object and the next run would bake that in as the rest pose. Stash it once.
def capture_base(objects, force=False):
    """Return {name: (location, quaternion)}, persisted on the object itself."""
    from mathutils import Vector, Quaternion
    base = {}
    for ob in objects:
        if force or "lw_base_loc" not in ob:
            q = (ob.rotation_quaternion.copy() if ob.rotation_mode == "QUATERNION"
                 else ob.rotation_euler.to_quaternion())
            ob["lw_base_loc"] = list(ob.location)
            ob["lw_base_quat"] = list(q)
        base[ob.name] = (Vector(ob["lw_base_loc"][:]), Quaternion(ob["lw_base_quat"][:]))
    return base

def restore_base(objects):
    base = capture_base(objects)
    for ob in objects:
        loc, quat = base[ob.name]
        ob.rotation_mode = "QUATERNION"
        ob.location, ob.rotation_quaternion = loc.copy(), quat.copy()
    bpy.context.view_layer.update()
    return base
