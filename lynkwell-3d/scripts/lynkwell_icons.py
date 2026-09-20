"""Lynkwell Digital - shared icon system for Asset 2 (six service icons).

Every icon is built in the XZ plane facing -Y (so it faces the camera once glTF
converts to +Y up), normalised to the same bounding size, given the same corner
rounding and bevel, and animated with the same rigid 180-frame idle.
"""
import bpy, bmesh, math, sys
from mathutils import Vector, Quaternion, Euler, Matrix

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L

ROOT       = "/Users/jackdworkin/Claude Code Projects/lynkwell-3d"
TARGET_DIM = 0.96      # every icon normalised to this max bounding dimension
BEVEL_W    = 0.012     # identical soft edge on all six
BEVEL_SEG  = 3
CORNER_R   = 0.055     # identical silhouette corner rounding
CORNER_SEG = 5

# ------------------------------------------------------------------ 2D shapes
def round_corners(pts, r=CORNER_R, seg=CORNER_SEG):
    """Round every corner of a simple 2D polygon, clamped to the adjacent edges."""
    n, out = len(pts), []
    for i in range(n):
        p = Vector(pts[i - 1]); v = Vector(pts[i]); q = Vector(pts[(i + 1) % n])
        d1, d2 = (p - v), (q - v)
        l1, l2 = d1.length, d2.length
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        d1 /= l1; d2 /= l2
        cosang = max(-1.0, min(1.0, d1.dot(d2)))
        ang = math.acos(cosang)
        if ang > math.radians(176) or ang < math.radians(4):
            out.append(tuple(v)); continue
        t = min(r / math.tan(ang / 2), 0.45 * l1, 0.45 * l2)
        rr = t * math.tan(ang / 2)
        bis = (d1 + d2)
        if bis.length < 1e-9:
            out.append(tuple(v)); continue
        bis.normalize()
        c = v + bis * (rr / math.sin(ang / 2))
        a0 = (v + d1 * t) - c
        a1 = (v + d2 * t) - c
        start = math.atan2(a0.y, a0.x)
        end = math.atan2(a1.y, a1.x)
        d = (end - start + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            th = start + d * k / seg
            out.append((c.x + rr * math.cos(th), c.y + rr * math.sin(th)))
    return out

def rect_pts(w, h, r=CORNER_R):
    return round_corners([(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)], r)

def circle_pts(radius, seg=44):
    return [(radius * math.cos(2*math.pi*k/seg), radius * math.sin(2*math.pi*k/seg))
            for k in range(seg)]

def tri_pts(w, h, r=CORNER_R):
    return round_corners([(-w/2, -h/2), (w/2, -h/2), (0.0, h/2)], r)

def arrow_pts(length, thick, head_w, head_h, r=0.022):
    hl = length / 2
    return round_corners([
        (-hl, -thick), (hl - head_w, -thick), (hl - head_w, -head_h),
        (hl, 0.0), (hl - head_w, head_h), (hl - head_w, thick), (-hl, thick)], r)

def shield_pts(w, h, seg=18, r=0.05):
    top = h / 2
    pts = [(-w/2, top), (w/2, top)]
    for k in range(1, seg + 1):                      # right flank down to the point
        s = k / seg
        pts.append(((w/2) * (1 - s ** 2.2) ** 0.55, top - s * h))
    for k in range(seg - 1, 0, -1):                  # mirrored left flank
        s = k / seg
        pts.append((-(w/2) * (1 - s ** 2.2) ** 0.55, top - s * h))
    return round_corners(pts, r)

# ------------------------------------------------------------------ 3D meshes
def prism_mesh(name, pts, depth):
    """Extrude a closed 2D polygon (x, z) along Y. Front face looks toward -Y."""
    bm = bmesh.new()
    front = [bm.verts.new((x, -depth/2, z)) for x, z in pts]
    back  = [bm.verts.new((x,  depth/2, z)) for x, z in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    return L.mesh_from_bm(bm, name)

def torus_mesh(name, major_r, minor_r, major_seg=40, minor_seg=10, axis="Z"):
    bm = bmesh.new()
    rings = []
    for i in range(major_seg):
        a = 2 * math.pi * i / major_seg
        ca, sa = math.cos(a), math.sin(a)
        ring = []
        for j in range(minor_seg):
            b = 2 * math.pi * j / minor_seg
            rr = major_r + minor_r * math.cos(b)
            off = minor_r * math.sin(b)
            p = (rr*ca, rr*sa, off) if axis == "Z" else (rr*ca, off, rr*sa)
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for i in range(major_seg):
        ra, rb = rings[i], rings[(i + 1) % major_seg]
        for j in range(minor_seg):
            k = (j + 1) % minor_seg
            f = bm.faces.new((ra[j], rb[j], rb[k], ra[k]))
            f.smooth = True
    return L.mesh_from_bm(bm, name)

def revolve_mesh(name, profile, seg=40):
    """Open surface of revolution about Z. profile = [(radius, z), ...]."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        ra, rb = rings[i], rings[i + 1]
        for j in range(seg):
            k = (j + 1) % seg
            f = bm.faces.new((ra[j], ra[k], rb[k], rb[j]))
            f.smooth = True
    return L.mesh_from_bm(bm, name)

# ------------------------------------------------------------------ finishing
def add_icon_bevel(ob, width=BEVEL_W):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width, m.segments = width, BEVEL_SEG
    m.limit_method, m.angle_limit = "ANGLE", math.radians(30)
    m.use_clamp_overlap = True
    m.miter_outer = "MITER_ARC"
    return m

def normalise(objects, target=TARGET_DIM):
    """Uniformly scale mesh data + locations so the group's max dim == target,
    then centre it on the origin. Run BEFORE bevels so widths stay comparable."""
    bpy.context.view_layer.update()
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
    for ob in objects:
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])
    size = hi - lo
    s = target / max(size)
    mid = (lo + hi) * 0.5
    for ob in objects:
        for v in ob.data.vertices:
            v.co *= s
        ob.data.update()
        ob.location = (ob.location - mid) * s
    bpy.context.view_layer.update()
    return s, [round(v * s, 4) for v in size]

# ------------------------------------------------------------------ idle anim
IDLE_LEN, IDLE_KEYS = 180, 19
YAW, PITCH, BOB = math.radians(12.0), math.radians(2.5), 0.024

def _cyc(t, amp, ph):
    return amp * (math.sin(2 * math.pi * t + ph) - math.sin(ph))

def idle_pose(base_loc, base_quat, t):
    """Rigid: the whole icon turns and bobs as one, so nothing can separate."""
    yaw = YAW * math.sin(2 * math.pi * t)
    pitch = _cyc(t, PITCH, 0.9)
    bob = BOB * math.sin(4 * math.pi * t)
    gq = Euler((pitch, 0.0, yaw), "XYZ").to_quaternion()
    return gq @ base_loc + Vector((0.0, 0.0, bob)), gq @ base_quat

def _all_fcurves(action):
    if getattr(action, "layers", None):
        for layer in action.layers:
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []):
                    for fc in cb.fcurves:
                        yield fc
    else:
        for fc in action.fcurves:
            yield fc

def build_idle(objects):
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.render.fps = 0, IDLE_LEN, 24
    base = L.capture_base(objects, force=True)
    for ob in objects:
        act = bpy.data.actions.new(f"{ob.name}|idle")
        ob.animation_data_create().action = act
        loc0, quat0 = base[ob.name]
        for k in range(IDLE_KEYS):
            t = k / (IDLE_KEYS - 1)
            ob.location, ob.rotation_quaternion = idle_pose(loc0, quat0, t)
            ob.keyframe_insert("location", frame=round(t * IDLE_LEN))
            ob.keyframe_insert("rotation_quaternion", frame=round(t * IDLE_LEN))
        for fc in _all_fcurves(act):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
        ad = ob.animation_data
        trk = ad.nla_tracks.new(); trk.name = "idle"
        strip = trk.strips.new("idle", 0, act); strip.name = "idle"
        if hasattr(strip, "action_slot") and strip.action_slot is None and len(act.slots):
            strip.action_slot = act.slots[0]
        ad.action = None
    L.restore_base(objects)
    for ob in objects:
        for t_ in ob.animation_data.nla_tracks:
            t_.mute = True
    sc.frame_set(0)
    seam = max((idle_pose(*base[o.name], 0.0)[0] - idle_pose(*base[o.name], 1.0)[0]).length
               for o in objects)
    return round(seam, 9)

# ------------------------------------------------------------------ preview rig
def build_rig(floor_z=-0.66):
    sc = bpy.context.scene
    rig = L.get_collection("preview_rig")
    world = bpy.data.worlds.new("lynkwell_world")
    sc.world = world
    world.use_nodes = True
    bgn = world.node_tree.nodes["Background"]
    bgn.inputs[0].default_value = (*L.hexlin(L.HEX["bg"]), 1.0)
    bgn.inputs[1].default_value = 1.0

    bm = bmesh.new()
    h = 13.0
    vs = [bm.verts.new(v) for v in ((-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0))]
    bm.faces.new(vs)
    floor = bpy.data.objects.new("preview_backdrop", L.mesh_from_bm(bm, "preview_backdrop"))
    rig.objects.link(floor)
    floor.location = (0.0, 0.0, floor_z)
    floor.is_shadow_catcher = True

    def area(name, size, energy, loc):
        d = bpy.data.lights.new(name, "AREA")
        d.shape, d.size, d.energy = "SQUARE", size, energy
        ob = bpy.data.objects.new(name, d)
        rig.objects.link(ob)
        ob.location = Vector(loc)
        ob.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area("key_light",  4.0, 105.0, (2.1, -2.8, 2.3))
    area("fill_light", 5.4,  40.0, (-3.0, -2.1, 0.35))
    area("rim_light",  2.6,  52.0, (-0.7, 2.3, 2.8))

    cd = bpy.data.cameras.new("preview_cam")
    cd.lens, cd.sensor_width = 85.0, 36.0
    cam = bpy.data.objects.new("preview_cam", cd)
    rig.objects.link(cam)
    cam.location = Vector((0.62, -4.30, 0.55))
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam

    sc.render.engine = "CYCLES"
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.device = "GPU"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    return rig

def ui_override():
    """Right after read_homefile the screen context is half-built and
    bpy.context.active_object vanishes, which the glTF exporter requires.
    Hand the operators a complete window/screen/area context explicitly."""
    wms = list(bpy.data.window_managers)
    if not wms or not wms[0].windows:
        return {}
    win = wms[0].windows[0]
    scr = win.screen
    ov = {"window": win, "screen": scr}
    areas = list(scr.areas) if scr else []
    area = next((a for a in areas if a.type == "VIEW_3D"), areas[0] if areas else None)
    if area:
        ov["area"] = area
        rgn = next((r for r in area.regions if r.type == "WINDOW"), None)
        if rgn:
            ov["region"] = rgn
    return ov

def run_op(fn, **kw):
    ov = ui_override()
    if ov:
        with bpy.context.temp_override(**ov):
            return fn(**kw)
    return fn(**kw)

def export_icon(objects, stem):
    import os
    for ob in objects:
        if ob.animation_data:
            for t in ob.animation_data.nla_tracks:
                t.mute = False
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    glb = f"{ROOT}/export/{stem}.glb"
    run_op(bpy.ops.export_scene.gltf,
        filepath=glb, export_format="GLB", use_selection=True, export_apply=True,
        export_yup=True, export_cameras=False, export_lights=False,
        export_materials="EXPORT", export_extras=False,
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
        export_animations=True, export_animation_mode="NLA_TRACKS",
        export_force_sampling=True, export_optimize_animation_size=True,
        export_frame_range=False, export_nla_strips=True)
    for ob in objects:
        if ob.animation_data:
            for t in ob.animation_data.nla_tracks:
                t.mute = True
    bpy.context.scene.frame_set(0)
    L.restore_base(objects)          # tracks were live during export - reset the rest pose
    blend = f"{ROOT}/blend/{stem}.blend"
    run_op(bpy.ops.wm.save_as_mainfile, filepath=blend)
    return glb, blend, round(os.path.getsize(glb) / 1024, 1)
