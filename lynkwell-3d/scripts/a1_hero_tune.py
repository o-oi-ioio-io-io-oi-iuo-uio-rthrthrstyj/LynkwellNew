"""Asset 1 - lighting/framing tuning pass with measured exposure."""
import bpy, math, sys, importlib, time
from mathutils import Vector

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L
importlib.reload(L)

sc = bpy.context.scene

# ---- backdrop -> shadow catcher: bone background everywhere, shadow only ----
floor = bpy.data.objects["preview_backdrop"]
floor.is_shadow_catcher = True
floor.location.z = -0.86

# ---- dial lights down to near-albedo exposure -------------------------------
ENERGY = {"key_light": 150.0, "fill_light": 55.0, "rim_light": 70.0}
for n, e in ENERGY.items():
    bpy.data.objects[n].data.energy = e

# ---- beef up the node cluster so the open side of the arc has presence ------
for name, rad in (("hero_node_01", 0.085), ("hero_node_02", 0.062), ("hero_node_03", 0.048)):
    ob = bpy.data.objects[name]
    old = bpy.data.meshes[name + "_mesh"]
    ob.data = L.sphere_mesh(name + "_mesh_v2", rad)
    bpy.data.meshes.remove(old)
bpy.data.objects["hero_node_02"].location.x = -0.575

for n in ("hero_rod_01", "hero_rod_02", "hero_rod_03", "hero_rod_04"):
    ob = bpy.data.objects[n]
    me = ob.data
    sx = 0.014 / 0.011
    for v in me.vertices:            # widen the rods in their own local XY
        v.co.x *= sx
        v.co.y *= sx
    me.update()

bpy.context.view_layer.update()

def render_stats(path, res=(640, 480), samples=32):
    rx, ry, sm = sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples
    sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = res[0], res[1], samples
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = rx, ry, sm

    img = bpy.data.images.load(path, check_existing=False)
    px = list(img.pixels)
    n = len(px) // 4
    lum = [0.2126 * px[i*4] + 0.7152 * px[i*4+1] + 0.0722 * px[i*4+2] for i in range(n)]
    clipped = sum(1 for v in lum if v >= 0.995) / n
    srt = sorted(lum)
    bpy.data.images.remove(img)
    return {"seconds": round(dt, 1), "clipped_frac": round(clipped, 4),
            "p50": round(srt[n//2], 3), "p95": round(srt[int(n*0.95)], 3),
            "max": round(srt[-1], 3)}

TMP = "/private/tmp/claude-501/-Users-jackdworkin-Claude-Code-Projects/e918487a-fd73-4c4e-91af-831a93eaa44e/scratchpad"
result = render_stats(TMP + "/hero_t2.png")
