"""Asset 4 - Statement object: "Your website should earn its place".

An oversized chain link rendered as a monolith: a stadium loop swept with a
chunky rectangular section, charcoal satin, with a thin cobalt inlay line
running the full loop on both faces. One mesh, two material slots, so the
inlay can never drift from the body. Slow 360 deg rotation over 300 frames.
"""
import bpy, bmesh, math, sys, importlib, time, os
from mathutils import Vector

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L; importlib.reload(L)
import lynkwell_icons as I; importlib.reload(I)

ROOT = "/Users/jackdworkin/Claude Code Projects/lynkwell-3d"

A, E   = 0.255, 0.480      # stadium centreline: cap radius, straight run
W, D   = 0.105, 0.150      # section half-thickness (radial) / half-depth (Y)
G      = 0.016             # cobalt inlay half-width
CORNER_R, CORNER_SEG = 0.018, 6
N_SEMI, N_STRAIGHT = 24, 4
SPIN_FRAMES = 300

# outer 0.72 w x 1.20 h x 0.30 d, void 0.30 x 0.78

# ------------------------------------------------------------------ profile
def round_tagged(pts, mats, r, seg):
    """Round corners of a tagged 2D profile, carrying the per-segment material."""
    out_p, out_m, n = [], [], len(pts)
    for i in range(n):
        p, v, q = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        d1, d2 = p - v, q - v
        l1, l2 = d1.length, d2.length
        d1 /= l1; d2 /= l2
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if ang > math.radians(176):                 # inserted collinear split point
            out_p.append(tuple(v)); out_m.append(mats[i])
            continue
        t = min(r / math.tan(ang / 2), 0.45 * l1, 0.45 * l2)
        rr = t * math.tan(ang / 2)
        c = v + (d1 + d2).normalized() * (rr / math.sin(ang / 2))
        a0, a1 = (v + d1 * t) - c, (v + d2 * t) - c
        s0, s1 = math.atan2(a0.y, a0.x), math.atan2(a1.y, a1.x)
        dd = (s1 - s0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            th = s0 + dd * k / seg
            out_p.append((c.x + rr * math.cos(th), c.y + rr * math.sin(th)))
            out_m.append(mats[i - 1] if k < seg else mats[i])
    return out_p, out_m

def section():
    """(u,v) section: u = radial, v = depth. Front/back faces split at +/-G
    so the middle band can carry the cobalt material - a flush, true inlay."""
    sharp = [(-W, -D), (-G, -D), (G, -D), (W, -D),
             ( W, -G), ( W,  G), ( W,  D),
             ( G,  D), (-G,  D), (-W,  D)]
    #        front face ->|        |<- outer rim ->|   |<- back face
    mats  = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0]   # 0 charcoal, 1 cobalt
    # the rim band matters: edge-on, the face inlays disappear and the piece
    # would otherwise read as a blank slab for a quarter of the rotation
    return round_tagged(sharp, mats, CORNER_R, CORNER_SEG)

def stadium_path():
    pts = []
    for k in range(N_STRAIGHT):                      # right run, upward
        pts.append(Vector((A, 0.0, -E / 2 + E * k / N_STRAIGHT)))
    for k in range(N_SEMI):                          # top cap
        th = math.pi * k / N_SEMI
        pts.append(Vector((A * math.cos(th), 0.0, E / 2 + A * math.sin(th))))
    for k in range(N_STRAIGHT):                      # left run, downward
        pts.append(Vector((-A, 0.0, E / 2 - E * k / N_STRAIGHT)))
    for k in range(N_SEMI):                          # bottom cap
        th = math.pi + math.pi * k / N_SEMI
        pts.append(Vector((A * math.cos(th), 0.0, -E / 2 + A * math.sin(th))))
    return pts

def sweep_mesh(name):
    path = stadium_path()
    prof, pmat = section()
    npa, npr = len(path), len(prof)
    N = Vector((0.0, 1.0, 0.0))
    bm = bmesh.new()
    rings = []
    for i, P in enumerate(path):
        T = (path[(i + 1) % npa] - path[i - 1]).normalized()
        S = N.cross(T).normalized()                  # points radially outward
        rings.append([bm.verts.new(P + S * u + N * v) for (u, v) in prof])
    bm.verts.ensure_lookup_table()
    for i in range(npa):
        ra, rb = rings[i], rings[(i + 1) % npa]
        for j in range(npr):
            k = (j + 1) % npr
            f = bm.faces.new((ra[j], rb[j], rb[k], ra[k]))
            f.material_index = pmat[j]
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.mesh_from_bm(bm, name), npa, npr

# ------------------------------------------------------------------ build
def run(render=True):
    L.reset_scene()
    m = L.brand_materials()
    col = L.get_collection("lynkwell_statement")

    me, npa, npr = sweep_mesh("statement_link")
    ob = L.new_object("statement_link", me, col)
    ob.data.materials.append(m["mat_charcoal"])
    ob.data.materials.append(m["mat_cobalt"])

    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.render.fps = 0, SPIN_FRAMES, 24

    # ---- slow 360 deg turn about the vertical axis, exactly constant speed --
    ob.rotation_mode = "XYZ"
    act = bpy.data.actions.new("statement_link|rotate_360")
    ob.animation_data_create().action = act
    for f, ang in ((0, 0.0), (SPIN_FRAMES, 2 * math.pi)):
        ob.rotation_euler = (0.0, 0.0, ang)
        ob.keyframe_insert("rotation_euler", frame=f)
    for fc in I._all_fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"              # constant angular velocity
    ad = ob.animation_data
    trk = ad.nla_tracks.new(); trk.name = "rotate_360"
    strip = trk.strips.new("rotate_360", 0, act); strip.name = "rotate_360"
    if hasattr(strip, "action_slot") and strip.action_slot is None and len(act.slots):
        strip.action_slot = act.slots[0]
    ad.action = None
    ob.rotation_euler = (0.0, 0.0, 0.0)

    # ---- museum lighting: low key angle, strong rim to lift charcoal off cream
    I.build_rig(floor_z=-0.601)
    for n, e in (("key_light", 150.0), ("fill_light", 30.0), ("rim_light", 190.0)):
        bpy.data.objects[n].data.energy = e
    key = bpy.data.objects["key_light"]
    key.location = Vector((-2.40, -2.60, 2.40))
    key.rotation_euler = (Vector((0, 0, 0)) - key.location).to_track_quat("-Z", "Y").to_euler()
    rim = bpy.data.objects["rim_light"]
    rim.location = Vector((1.90, 2.40, 1.50))
    rim.rotation_euler = (Vector((0, 0, 0)) - rim.location).to_track_quat("-Z", "Y").to_euler()
    fill = bpy.data.objects["fill_light"]
    fill.location = Vector((3.00, -2.00, 0.30))
    fill.rotation_euler = (Vector((0, 0, 0)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    cam = bpy.data.objects["preview_cam"]
    cam.location = Vector((1.10, -4.10, -0.05))
    cam.rotation_euler = (Vector((0, 0, 0.06)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 900, 1200
    sc.cycles.samples = 96
    bpy.context.view_layer.update()

    tris, per = L.tri_count([ob])
    bb = [Vector(c) for c in ob.bound_box]
    size = [round(max(p[i] for p in bb) - min(p[i] for p in bb), 3) for i in range(3)]
    centre = [round((max(p[i] for p in bb) + min(p[i] for p in bb)) / 2, 4) for i in range(3)]
    cobalt_faces = sum(1 for p in me.polygons if p.material_index == 1)

    # ---- export (track live), then reset the rest pose ---------------------
    for t in ob.animation_data.nla_tracks:
        t.mute = False
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    glb = f"{ROOT}/export/statement_link.glb"
    I.run_op(bpy.ops.export_scene.gltf,
             filepath=glb, export_format="GLB", use_selection=True, export_apply=True,
             export_yup=True, export_cameras=False, export_lights=False,
             export_materials="EXPORT", export_extras=False,
             export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
             export_animations=True, export_animation_mode="NLA_TRACKS",
             export_force_sampling=True, export_optimize_animation_size=True,
             export_frame_range=False, export_nla_strips=True)
    for t in ob.animation_data.nla_tracks:
        t.mute = True
    sc.frame_set(0)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    blend = f"{ROOT}/blend/statement_link.blend"
    I.run_op(bpy.ops.wm.save_as_mainfile, filepath=blend)

    secs = 0.0
    if render:
        sc.render.filepath = f"{ROOT}/previews/statement_link.png"
        t0 = time.time()
        I.run_op(bpy.ops.render.render, write_still=True)
        secs = round(time.time() - t0, 1)

    return {"tris": tris, "path_pts": npa, "profile_pts": npr,
            "cobalt_faces": cobalt_faces, "total_faces": len(me.polygons),
            "cobalt_face_pct": round(100 * cobalt_faces / len(me.polygons), 1),
            "size": size, "centre": centre,
            "glb_kb": round(os.path.getsize(glb) / 1024, 1), "render_s": secs}
