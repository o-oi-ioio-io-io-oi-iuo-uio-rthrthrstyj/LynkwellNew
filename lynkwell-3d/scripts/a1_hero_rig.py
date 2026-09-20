"""Asset 1 - interlock verification + studio preview rig (lights/camera/backdrop)."""
import bpy, math, sys, importlib
from mathutils import Vector

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L
importlib.reload(L)

D = math.radians
A, E, R = 0.098, 0.170, 0.032
sc   = bpy.context.scene
hero = bpy.data.collections["lynkwell_hero"]
rig  = L.get_collection("preview_rig")
mats = L.brand_materials()
links = [bpy.data.objects[f"hero_link_{i:02d}"] for i in range(1, 8)]

# ---- topological interlock test -------------------------------------------
def seg_dist(px, py, half):
    return math.hypot(max(abs(px) - half, 0.0), py)

def path_points(ob, n=400):
    """Re-derive the stadium centreline in world space (mesh is a tube around it)."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        # parametrise the stadium by angle-ish sweep: use the four segments
        s = t / (2 * math.pi) * (2 * math.pi * A + 2 * E)
        arc = math.pi * A
        if s < arc:                       # right cap
            ang = -math.pi / 2 + s / A
            p = Vector((E / 2 + A * math.cos(ang), A * math.sin(ang), 0))
        elif s < arc + E:                 # top run
            p = Vector((E / 2 - (s - arc), A, 0))
        elif s < 2 * arc + E:             # left cap
            ang = math.pi / 2 + (s - arc - E) / A
            p = Vector((-E / 2 + A * math.cos(ang), A * math.sin(ang), 0))
        else:                             # bottom run
            p = Vector((-E / 2 + (s - 2 * arc - E), -A, 0))
        pts.append(ob.matrix_world @ p)
    return pts

interlocked = []
for i in range(len(links) - 1):
    a_inv = links[i].matrix_world.inverted()
    pts = [a_inv @ p for p in path_points(links[i + 1])]
    hit = False
    for j in range(len(pts)):
        p, q = pts[j], pts[(j + 1) % len(pts)]
        if p.z * q.z <= 0 and abs(p.z - q.z) > 1e-9:       # crosses link i's plane
            u = p.z / (p.z - q.z)
            x, y = p.x + u * (q.x - p.x), p.y + u * (q.y - p.y)
            if seg_dist(x, y, E / 2) < A - R:              # inside the hole
                hit = True
                break
    interlocked.append(hit)

# ---- world -----------------------------------------------------------------
world = bpy.data.worlds.new("lynkwell_world")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (*L.hexlin(L.HEX["bg"]), 1.0)
bg.inputs[1].default_value = 1.0

# ---- backdrop (preview only, never exported) --------------------------------
bpy.ops.mesh.primitive_plane_add(size=26.0, location=(0, 0, -0.95))
floor = bpy.context.object
floor.name = "preview_backdrop"
for c in floor.users_collection:
    c.objects.unlink(floor)
rig.objects.link(floor)
floor.data.materials.append(L.make_material("mat_preview_bg", L.HEX["bg"], 0.9))

# ---- lights -----------------------------------------------------------------
def area_light(name, size, energy, loc, target=Vector((0, 0, 0))):
    d = bpy.data.lights.new(name, "AREA")
    d.shape, d.size, d.energy = "SQUARE", size, energy
    ob = bpy.data.objects.new(name, d)
    rig.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob

area_light("key_light",  4.5, 900.0, (2.4, -3.2,  2.6))
area_light("fill_light", 6.0, 260.0, (-3.4, -2.4, 0.4))
area_light("rim_light",  3.0, 320.0, (-0.8,  2.6, 3.2))

# ---- camera -------------------------------------------------------------------
cd = bpy.data.cameras.new("preview_cam")
cd.lens, cd.sensor_width = 85.0, 36.0
cam = bpy.data.objects.new("preview_cam", cd)
rig.objects.link(cam)
cam.location = Vector((0.95, -4.90, 0.85))
cam.rotation_euler = (Vector((0.0, -0.03, 0.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

# ---- render settings -------------------------------------------------------------
sc.render.engine = "CYCLES"
sc.render.resolution_x, sc.render.resolution_y = 1400, 1050
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.film_transparent = False
sc.cycles.samples = 96
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.view_settings.exposure = 0.0

devices = []
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for ctype in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = ctype
            prefs.get_devices()
            found = [d.name for d in prefs.devices if d.type == ctype]
            if found:
                for d in prefs.devices:
                    d.use = True
                sc.cycles.device = "GPU"
                devices = [ctype] + found
                break
        except Exception:
            continue
except Exception as ex:
    devices = ["cpu-fallback:" + str(ex)]
if not devices:
    sc.cycles.device = "CPU"

result = {
    "interlocked_pairs": interlocked,
    "all_interlocked": all(interlocked),
    "cycles_device": sc.cycles.device,
    "devices": devices,
    "camera": [round(v, 2) for v in cam.location],
}
