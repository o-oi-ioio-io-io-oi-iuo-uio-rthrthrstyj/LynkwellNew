"""Re-render the six service icons on a transparent film for web fallbacks."""
import bpy, sys, importlib, time, os
sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_icons as I; importlib.reload(I)

ROOT = I.ROOT
OUT = ROOT + "/previews/web"
os.makedirs(OUT, exist_ok=True)

STEMS = ["icon_01_web_design", "icon_02_brand_identity", "icon_03_seo_performance",
         "icon_04_mobile_first", "icon_05_conversion", "icon_06_support"]

def run(indices, size=384, samples=64):
    out = []
    for i in indices:
        stem = STEMS[i]
        I.run_op(bpy.ops.wm.open_mainfile, filepath=f"{ROOT}/blend/{stem}.blend")
        sc = bpy.context.scene
        # transparent film + no backdrop = a clean cutout that sits on any card colour
        sc.render.film_transparent = True
        sc.render.image_settings.color_mode = "RGBA"
        bd = bpy.data.objects.get("preview_backdrop")
        if bd:
            bd.hide_render = True
        sc.render.resolution_x = sc.render.resolution_y = size
        sc.cycles.samples = samples
        sc.frame_set(0)
        path = f"{OUT}/{stem}.png"
        sc.render.filepath = path
        t0 = time.time()
        I.run_op(bpy.ops.render.render, write_still=True)
        out.append({"stem": stem, "s": round(time.time() - t0, 1),
                    "kb": round(os.path.getsize(path) / 1024, 1)})
    return out
