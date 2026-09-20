"""Asset 5 - Background accent: a sparse node field for the About/Contact sections.

24 tiny nodes on a Poisson-ish scatter, linked to near neighbours by thin rods.
One mesh, two material slots (stone + 3 cobalt nodes). No animation - the brief
doesn't call for one on this asset. Budget: under 3k triangles.
"""
import bpy, bmesh, math, random, sys, importlib, time, os
from mathutils import Vector, Matrix

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L; importlib.reload(L)
import lynkwell_icons as I; importlib.reload(I)

ROOT = "/Users/jackdworkin/Claude Code Projects/lynkwell-3d"
SX, SY, SZ = 3.00, 0.50, 1.70      # field extent (wide, shallow - it's a backdrop)
N_NODES    = 26
MIN_D      = 0.34                  # spacing measured in the VIEWED plane (XZ)
LINK_MAX   = 0.80                  # only near neighbours get linked
MAX_EDGES  = 30
MAX_DEGREE = 3
ROD_R      = 0.006
N_COBALT   = 3

def scatter(seed=5):
    """Rejection sampling with a relaxing radius so it always fills."""
    rnd = random.Random(seed)
    pts, min_d = [], MIN_D
    tries = 0
    while len(pts) < N_NODES:
        p = Vector((rnd.uniform(-SX/2, SX/2), rnd.uniform(-SY/2, SY/2), rnd.uniform(-SZ/2, SZ/2)))
        # measure spacing in XZ only: a 3D test lets points stack in depth and
        # the field then reads as clumps from the camera
        if all(math.hypot(p.x - q.x, p.z - q.z) > min_d for q in pts):
            pts.append(p)
        tries += 1
        if tries % 4000 == 0:
            min_d *= 0.92
    return pts, round(min_d, 4)

def link(pts):
    pairs = []
    for i in range(len(pts)):
        for k in range(i + 1, len(pts)):
            d = (pts[i] - pts[k]).length
            if d < LINK_MAX:
                pairs.append((d, i, k))
    pairs.sort()
    deg = [0] * len(pts)
    adj = [set() for _ in pts]
    edges = []
    for d, i, k in pairs:
        if len(edges) >= MAX_EDGES:
            break
        if deg[i] >= MAX_DEGREE or deg[k] >= MAX_DEGREE:
            continue
        if adj[i] & adj[k]:          # would close a triangle -> reads as a tangle
            continue
        edges.append((i, k)); deg[i] += 1; deg[k] += 1
        adj[i].add(k); adj[k].add(i)
    for i in range(len(pts)):                       # no orphans
        if deg[i] == 0:
            k = min((x for x in range(len(pts)) if x != i),
                    key=lambda x: (pts[i] - pts[x]).length)
            edges.append((i, k)); deg[i] += 1; deg[k] += 1
            adj[i].add(k); adj[k].add(i)
    return edges, deg

def pick_cobalt(pts, deg):
    """Three well-separated hub nodes, one per horizontal third."""
    out = []
    for lo, hi in ((-SX/2, -SX/6), (-SX/6, SX/6), (SX/6, SX/2)):
        band = [i for i, p in enumerate(pts) if lo <= p.x < hi]
        if band:
            out.append(max(band, key=lambda i: (deg[i], pts[i].z)))
    return out[:N_COBALT]

def ico(bm, centre, r):
    try:
        ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    except TypeError:
        ret = bmesh.ops.create_icosphere(bm, subdivisions=2, diameter=r)
    bmesh.ops.translate(bm, vec=centre, verts=ret["verts"])
    return ret["verts"]

def rod(bm, p0, p1, r, sides=6):
    d = p1 - p0
    M = Matrix.Translation((p0 + p1) * 0.5) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    ret = bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=sides,
                                radius1=r, radius2=r, depth=d.length)
    bmesh.ops.transform(bm, matrix=M, verts=ret["verts"])
    return ret["verts"]

def run(render=True):
    L.reset_scene()
    m = L.brand_materials()
    col = L.get_collection("lynkwell_bg")

    pts, used_min_d = scatter()
    edges, deg = link(pts)
    cobalt = set(pick_cobalt(pts, deg))
    rnd = random.Random(17)

    bm = bmesh.new()
    face_mat = []            # material index per face, in creation order
    def tag(mi):
        # bmesh appends new faces, so everything past the last tagged index is new
        while len(face_mat) < len(bm.faces):
            face_mat.append(mi)

    for i, p in enumerate(pts):
        r = 0.042 if i in cobalt else rnd.uniform(0.022, 0.036)
        ico(bm, p, r)
        tag(1 if i in cobalt else 0)
    for a, b in edges:
        rod(bm, pts[a], pts[b], ROD_R)
        tag(0)

    bm.faces.ensure_lookup_table()
    for idx, f in enumerate(bm.faces):
        f.material_index = face_mat[idx]
        f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = L.mesh_from_bm(bm, "bg_node_field")

    lo = Vector((min(v.co[i] for v in me.vertices) for i in range(3)))
    hi = Vector((max(v.co[i] for v in me.vertices) for i in range(3)))
    mid = (lo + hi) * 0.5
    for v in me.vertices:
        v.co -= mid
    me.update()

    ob = L.new_object("bg_node_field", me, col)
    ob.data.materials.append(m["mat_stone"])
    ob.data.materials.append(m["mat_cobalt"])

    sc = bpy.context.scene
    I.build_rig(floor_z=-1.30)
    for n, e in (("key_light", 120.0), ("fill_light", 45.0), ("rim_light", 60.0)):
        bpy.data.objects[n].data.energy = e
    cam = bpy.data.objects["preview_cam"]
    cam.data.lens = 55.0
    cam.location = Vector((0.45, -5.55, 0.30))
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 1400, 800
    sc.cycles.samples = 72
    bpy.context.view_layer.update()

    tris, _ = L.tri_count([ob])
    bb = [Vector(c) for c in ob.bound_box]
    size = [round(max(q[i] for q in bb) - min(q[i] for q in bb), 3) for i in range(3)]
    centre = [round((max(q[i] for q in bb) + min(q[i] for q in bb)) / 2, 4) for i in range(3)]

    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    glb = f"{ROOT}/export/bg_node_field.glb"
    I.run_op(bpy.ops.export_scene.gltf,
             filepath=glb, export_format="GLB", use_selection=True, export_apply=True,
             export_yup=True, export_cameras=False, export_lights=False,
             export_materials="EXPORT", export_extras=False,
             export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
             export_animations=False)
    I.run_op(bpy.ops.wm.save_as_mainfile, filepath=f"{ROOT}/blend/bg_node_field.blend")

    secs = 0.0
    if render:
        sc.render.filepath = f"{ROOT}/previews/bg_node_field.png"
        t0 = time.time()
        I.run_op(bpy.ops.render.render, write_still=True)
        secs = round(time.time() - t0, 1)

    return {"nodes": len(pts), "edges": len(edges), "cobalt_nodes": sorted(cobalt),
            "degrees": deg, "scatter_min_dist": used_min_d,
            "tris": tris, "faces": len(me.polygons), "size": size, "centre": centre,
            "glb_kb": round(os.path.getsize(glb) / 1024, 1), "render_s": secs}
