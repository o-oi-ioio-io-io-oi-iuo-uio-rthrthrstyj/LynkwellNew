"""Asset 1 - restore node materials, re-anchor rods to link tips, final exposure."""
import bpy, math, sys, importlib, time
from mathutils import Vector

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L
importlib.reload(L)

sc   = bpy.context.scene
mats = L.brand_materials()
hero = bpy.data.collections["lynkwell_hero"]
A, E, R = 0.098, 0.170, 0.032
TIP     = E / 2 + A + R          # 0.215 - half the link's outer length
ROD_R   = 0.014

# ---- 1. node materials were lost when the meshes were swapped ---------------
for name, mat in (("hero_node_01", "mat_cream"),
                  ("hero_node_02", "mat_stone"),
                  ("hero_node_03", "mat_charcoal")):
    ob = bpy.data.objects[name]
    ob.data.materials.clear()
    ob.data.materials.append(mats[mat])

nodes = [bpy.data.objects[f"hero_node_{i:02d}"] for i in (1, 2, 3)]
links = [bpy.data.objects[f"hero_link_{i:02d}"] for i in range(1, 8)]
nodes[2].location.y = -0.030
nodes[0].location.y = -0.090
nodes[1].location.y = -0.160
bpy.context.view_layer.update()

def link_tip(link, toward):
    """World-space point just inside whichever end cap faces `toward`."""
    mw = link.matrix_world
    cands = [mw @ Vector((s * (TIP - 0.025), 0.0, 0.0)) for s in (1.0, -1.0)]
    return min(cands, key=lambda p: (p - toward).length)

# ---- 2. rebuild every rod at the new radius, anchored properly --------------
for n in ("hero_rod_01", "hero_rod_02", "hero_rod_03", "hero_rod_04"):
    ob = bpy.data.objects[n]
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)

def make_rod(name, p0, p1):
    d = p1 - p0
    ob = L.new_object(name, L.rod_mesh(name + "_mesh", ROD_R, d.length), hero, mats["mat_stone"])
    ob.location = (p0 + p1) * 0.5
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    L.add_bevel(ob, width=0.004)
    return ob

rods = [
    make_rod("hero_rod_01", link_tip(links[6], nodes[2].location), nodes[2].location.copy()),
    make_rod("hero_rod_02", nodes[2].location.copy(), nodes[0].location.copy()),
    make_rod("hero_rod_03", nodes[0].location.copy(), nodes[1].location.copy()),
    make_rod("hero_rod_04", nodes[0].location.copy(), link_tip(links[0], nodes[0].location)),
]

# ---- 3. exposure ------------------------------------------------------------
for n, e in (("key_light", 112.0), ("fill_light", 42.0), ("rim_light", 58.0)):
    bpy.data.objects[n].data.energy = e

assets = links + nodes + rods
bpy.context.view_layer.update()
total, per = L.tri_count(assets)

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
    lum = sorted(0.2126*px[i*4] + 0.7152*px[i*4+1] + 0.0722*px[i*4+2] for i in range(n))
    clip = sum(1 for v in lum if v >= 0.995) / n
    bpy.data.images.remove(img)
    return {"seconds": round(dt,1), "clipped_frac": round(clip,4),
            "p50": round(lum[n//2],3), "p99": round(lum[int(n*0.99)],3)}

TMP = "/private/tmp/claude-501/-Users-jackdworkin-Claude-Code-Projects/e918487a-fd73-4c4e-91af-831a93eaa44e/scratchpad"
result = {"stats": render_stats(TMP + "/hero_t3.png"),
          "tris_total": total, "objects": len(assets),
          "mats_per_object": {o.name: [m.name for m in o.data.materials] for o in assets}}
