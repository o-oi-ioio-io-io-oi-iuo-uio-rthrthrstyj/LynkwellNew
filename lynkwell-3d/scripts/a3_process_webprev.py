"""Transparent per-stage renders of the process scene, for the mobile list."""
import bpy, sys, importlib, time, os
sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_icons as I; importlib.reload(I)

ROOT = I.ROOT
OUT = ROOT + "/previews/web"
STATES = ["process_01_discovery", "process_02_design", "process_03_build", "process_04_launch"]

def run(size=512, samples=72):
    os.makedirs(OUT, exist_ok=True)
    I.run_op(bpy.ops.wm.open_mainfile, filepath=f"{ROOT}/blend/process_journey.blend")
    sc = bpy.context.scene
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    bd = bpy.data.objects.get("preview_backdrop")
    if bd:
        bd.hide_render = True
    sc.camera = bpy.data.objects["preview_cam"]
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.cycles.samples = samples
    sc.frame_set(0)

    states = [bpy.data.objects[n] for n in STATES]
    out = []
    for ob in states:
        for o in states:
            o.hide_render = (o is not ob)
        path = f"{OUT}/{ob.name}.png"
        sc.render.filepath = path
        t0 = time.time()
        I.run_op(bpy.ops.render.render, write_still=True)
        out.append({"name": ob.name, "s": round(time.time() - t0, 1),
                    "kb": round(os.path.getsize(path) / 1024, 1)})
    for o in states:
        o.hide_render = False
    return out
