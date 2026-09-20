"""Asset 3 - Process: Discovery -> Design -> Build -> Launch.

One abstract block structure expressed as four separate meshes stacked at the
same origin, so the site can crossfade between them. Plus a 'camera_path' empty
and an orbiting camera keyframed over 400 frames (100 per stage).
"""
import bpy, bmesh, math, sys, importlib, time, os
from mathutils import Vector, Matrix, Quaternion, Euler

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L; importlib.reload(L)
import lynkwell_icons as I; importlib.reload(I)

ROOT = "/Users/jackdworkin/Claude Code Projects/lynkwell-3d"
BEVEL_W, BEVEL_SEG = 0.016, 2
ROD_R, NODE_R = 0.011, 0.024
STAGE_FRAMES, N_STAGES = 100, 4
TOTAL_FRAMES = STAGE_FRAMES * N_STAGES        # 400

# name, size (x,y,z), centre, build-state material key
BLOCKS = [
    ("base",    (1.10, 0.80, 0.10), (0.00,  0.00, -0.50), "charcoal"),
    ("blk_a",   (0.44, 0.62, 0.34), (-0.28, 0.02, -0.28), "cream"),
    ("blk_b",   (0.38, 0.46, 0.34), (0.30, -0.08, -0.28), "stone"),
    ("blk_c",   (0.96, 0.58, 0.14), (0.00,  0.00, -0.04), "cream"),
    ("blk_d",   (0.34, 0.36, 0.42), (-0.26, 0.04,  0.24), "stone"),
    ("blk_e",   (0.28, 0.30, 0.18), (0.24, -0.04,  0.12), "charcoal"),
    ("blk_top", (0.22, 0.24, 0.22), (-0.26, 0.04,  0.56), "cobalt"),
]
Z_OFF = -0.06          # raw form spans z -0.55..0.67; shift so the group centres on 0
BLOCKS = [(n, s_, (c[0], c[1], c[2] + Z_OFF), k) for n, s_, c, k in BLOCKS]
RING_Z = -0.50 + Z_OFF

# ------------------------------------------------------------------ geometry
def bm_arrays(bm, smooth):
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces, smooth

def part_box(size, centre):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                    offset=BEVEL_W, segments=BEVEL_SEG, profile=0.5,
                    affect="EDGES", clamp_overlap=True)
    bmesh.ops.translate(bm, vec=Vector(centre), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_arrays(bm, False)

def part_rod(p0, p1, r, sides=6):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    M = Matrix.Translation((p0 + p1) * 0.5) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides,
                          radius1=r, radius2=r, depth=d.length)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_arrays(bm, True)

def part_sphere(c, r, u=8, v=4):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_arrays(bm, True)

def part_torus(major, minor, z, mseg=32, nseg=8):
    me = I.torus_mesh("tmp_torus", major, minor, mseg, nseg)
    verts = [(v.co.x, v.co.y, v.co.z + z) for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    bpy.data.meshes.remove(me)
    return verts, faces, True

def corners(size, centre):
    sx, sy, sz = (s / 2 for s in size)
    cx, cy, cz = centre
    return [(cx + (sx if i & 1 else -sx), cy + (sy if i & 2 else -sy), cz + (sz if i & 4 else -sz))
            for i in range(8)]

CUBE_EDGES = [(0,1),(2,3),(4,5),(6,7),(0,2),(1,3),(4,6),(5,7),(0,4),(1,5),(2,6),(3,7)]

def assemble(name, parts):
    """parts = [(verts, faces, smooth, material_index)] -> one multi-material mesh."""
    V, F, S, M = [], [], [], []
    for verts, faces, smooth, mi in parts:
        off = len(V)
        V.extend(verts)
        for f in faces:
            F.append(tuple(i + off for i in f))
            S.append(smooth)
            M.append(mi)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.validate()
    me.update()
    for i, p in enumerate(me.polygons):
        p.material_index = M[i]
        p.use_smooth = S[i]
    return me

# ------------------------------------------------------------------ states
def build_states(col, m):
    objs = []

    # ---- 01 discovery: charcoal edge rods + stone corner nodes --------------
    parts = []
    for _, size, centre, _ in BLOCKS:
        cs = corners(size, centre)
        for a, b in CUBE_EDGES:
            parts.append((*part_rod(cs[a], cs[b], ROD_R), 0))
        for c in cs:
            parts.append((*part_sphere(c, NODE_R), 1))
    ob = L.new_object("process_01_discovery", assemble("process_01_discovery", parts), col)
    for k in ("mat_charcoal", "mat_stone"):
        ob.data.materials.append(m[k])
    objs.append(ob)

    # ---- 02 design: the same form, plain cream solids -----------------------
    parts = [(*part_box(size, centre), 0) for _, size, centre, _ in BLOCKS]
    ob = L.new_object("process_02_design", assemble("process_02_design", parts), col)
    ob.data.materials.append(m["mat_cream"])
    objs.append(ob)

    # ---- 03 build: full material treatment, one cobalt block ----------------
    slot = {"cream": 0, "stone": 1, "charcoal": 2, "cobalt": 3}
    parts = [(*part_box(size, centre), slot[key]) for _, size, centre, key in BLOCKS]
    ob = L.new_object("process_03_build", assemble("process_03_build", parts), col)
    for k in ("mat_cream", "mat_stone", "mat_charcoal", "mat_cobalt"):
        ob.data.materials.append(m[k])
    objs.append(ob)

    # ---- 04 launch: build + glowing edge trim + a pulse ring at the base ----
    parts = [(*part_box(size, centre), slot[key]) for _, size, centre, key in BLOCKS]
    slab = next(b for b in BLOCKS if b[0] == "blk_c")
    cs = corners(slab[1], slab[2])
    for a, b in CUBE_EDGES:                                   # glowing outline
        parts.append((*part_rod(cs[a], cs[b], 0.018, 8), 4))
    parts.append((*part_torus(0.76, 0.016, RING_Z), 4))        # pulse ring
    ob = L.new_object("process_04_launch", assemble("process_04_launch", parts), col)
    for k in ("mat_cream", "mat_stone", "mat_charcoal", "mat_cobalt", "mat_cobalt_glow"):
        ob.data.materials.append(m[k])
    objs.append(ob)
    return objs

# ------------------------------------------------------------------ camera
R0, DR   = 3.50, 0.18
Z0, DZ   = 1.15, 0.40
AIM      = Vector((0.0, 0.0, 0.02))
THETA0   = -math.pi / 2          # frame 0 sits square in front of the structure

def orbit_at(t):
    th = THETA0 + 2 * math.pi * t
    r = R0 + DR * math.sin(2 * math.pi * t)
    z = Z0 + DZ * (math.sin(2 * math.pi * t + math.pi / 3) - math.sin(math.pi / 3))
    loc = Vector((r * math.cos(th), r * math.sin(th), z))
    return loc, (AIM - loc).to_track_quat("-Z", "Y")

def build_camera(col):
    empty = bpy.data.objects.new("camera_path", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.5
    col.objects.link(empty)

    cd = bpy.data.cameras.new("process_camera")
    cd.lens, cd.sensor_width = 70.0, 36.0
    cam = bpy.data.objects.new("process_camera", cd)
    col.objects.link(cam)
    cam.rotation_mode = "QUATERNION"

    act = bpy.data.actions.new("process_camera|camera_orbit")
    cam.animation_data_create().action = act
    for k in range(41):                                   # every 10 frames
        t = k / 40.0
        loc, quat = orbit_at(t)
        cam.location, cam.rotation_quaternion = loc, quat
        f = round(t * TOTAL_FRAMES)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
    for fc in I._all_fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    ad = cam.animation_data
    trk = ad.nla_tracks.new(); trk.name = "camera_orbit"
    strip = trk.strips.new("camera_orbit", 0, act); strip.name = "camera_orbit"
    if hasattr(strip, "action_slot") and strip.action_slot is None and len(act.slots):
        strip.action_slot = act.slots[0]
    ad.action = None

    # a visible reference curve in the .blend, sampled from the same orbit maths
    cu = bpy.data.curves.new("camera_path_curve", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(119)
    for k in range(120):
        loc, _ = orbit_at(k / 120.0)
        sp.points[k].co = (*loc, 1.0)
    sp.use_cyclic_u = True
    curve_ob = bpy.data.objects.new("camera_path_curve", cu)
    col.objects.link(curve_ob)
    return empty, cam, curve_ob


# ------------------------------------------------------------------ runner
def run(render=True):
    L.reset_scene()
    m = L.brand_materials()
    col = L.get_collection("lynkwell_process")
    states = build_states(col, m)
    empty, cam, curve = build_camera(col)

    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.render.fps = 0, TOTAL_FRAMES, 24

    I.build_rig(floor_z=-0.62)
    pv = bpy.data.objects["preview_cam"]
    pv.location = Vector((2.10, -3.60, 1.35))
    pv.rotation_euler = (Vector((0, 0, 0)) - pv.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = pv
    sc.render.resolution_x = sc.render.resolution_y = 900
    bpy.context.view_layer.update()

    tris, per = L.tri_count(states)

    # ---- export: the four states + the path empty + the orbit camera only ---
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    for ob in states + [empty, cam]:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = states[0]
    glb = f"{ROOT}/export/process_journey.glb"
    I.run_op(bpy.ops.export_scene.gltf,
             filepath=glb, export_format="GLB", use_selection=True, export_apply=True,
             export_yup=True, export_cameras=True, export_lights=False,
             export_materials="EXPORT", export_extras=False,
             export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
             export_animations=True, export_animation_mode="NLA_TRACKS",
             export_force_sampling=True, export_optimize_animation_size=True,
             export_frame_range=False, export_nla_strips=True)
    blend = f"{ROOT}/blend/process_journey.blend"
    I.run_op(bpy.ops.wm.save_as_mainfile, filepath=blend)

    # ---- one preview per state, from a single fixed 3/4 viewpoint -----------
    shots = []
    if render:
        for i, ob in enumerate(states):
            for other in states:
                other.hide_render = (other is not ob)
            png = f"{ROOT}/previews/{ob.name}.png"
            sc.render.filepath = png
            t0 = time.time()
            I.run_op(bpy.ops.render.render, write_still=True)
            shots.append((png, round(time.time() - t0, 1)))
        for ob in states:
            ob.hide_render = False

    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for ob in states:
        for c in ob.evaluated_get(dg).bound_box:
            w = ob.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])

    return {"tris_total": tris, "tris_per_state": per,
            "glb_kb": round(os.path.getsize(glb) / 1024, 1),
            "bbox_size": [round(v, 3) for v in (hi - lo)],
            "bbox_centre": [round(v, 3) for v in ((hi + lo) / 2)],
            "state_locations": {o.name: [round(v, 3) for v in o.location] for o in states},
            "renders": shots}
