"""Asset 2 - the six service icons. One .glb each, one shared visual system."""
import bpy, math, sys, importlib, time, os
from mathutils import Vector

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L; importlib.reload(L)
import lynkwell_icons as I; importlib.reload(I)

D = math.radians

def put(col, name, mesh, mat, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob = L.new_object(name, mesh, col, mat)
    ob.location = Vector(loc)
    ob.rotation_euler = rot
    return ob

# ------------------------------------------------------------------ 1. web
def build_web(col, m):
    o = []
    o.append(put(col, "icon_web_window", I.prism_mesh("web_window", I.rect_pts(0.80, 0.58), 0.08),
                 m["mat_cream"], (0.0, 0.05, 0.05)))
    o.append(put(col, "icon_web_header", I.prism_mesh("web_header", I.rect_pts(0.72, 0.11), 0.03),
                 m["mat_stone"], (0.0, -0.005, 0.265)))
    o.append(put(col, "icon_web_addressbar", I.prism_mesh("web_address", I.rect_pts(0.30, 0.05), 0.022),
                 m["mat_cobalt"], (0.04, -0.031, 0.265)))
    o.append(put(col, "icon_web_line_01", I.prism_mesh("web_line_01", I.rect_pts(0.32, 0.05), 0.028),
                 m["mat_stone"], (-0.20, -0.004, 0.10)))
    o.append(put(col, "icon_web_line_02", I.prism_mesh("web_line_02", I.rect_pts(0.22, 0.05), 0.028),
                 m["mat_stone"], (-0.25, -0.004, -0.02)))
    o.append(put(col, "icon_web_panel", I.prism_mesh("web_panel", I.rect_pts(0.44, 0.34), 0.07),
                 m["mat_charcoal"], (0.26, -0.17, -0.17)))
    return o

# ------------------------------------------------------------------ 2. brand
def build_brand(col, m):
    o = []
    o.append(put(col, "icon_brand_square", I.prism_mesh("brand_square", I.rect_pts(0.45, 0.45), 0.09),
                 m["mat_cream"], (-0.25, 0.08, -0.15)))
    o.append(put(col, "icon_brand_circle", I.prism_mesh("brand_circle", I.circle_pts(0.16), 0.09),
                 m["mat_cobalt"], (0.03, -0.05, 0.03)))
    o.append(put(col, "icon_brand_triangle", I.prism_mesh("brand_triangle", I.tri_pts(0.47, 0.42), 0.09),
                 m["mat_charcoal"], (0.27, 0.08, 0.20)))
    return o

# ------------------------------------------------------------------ 3. seo
def build_seo(col, m):
    o = [put(col, "icon_seo_baseline", I.prism_mesh("seo_base", I.rect_pts(0.92, 0.055), 0.10),
             m["mat_charcoal"], (0.0, 0.0, -0.42))]
    tops = [0.24, 0.38, 0.54, 0.72]
    cols = ["mat_stone", "mat_cream", "mat_stone", "mat_cream"]
    for i, (h, c) in enumerate(zip(tops, cols)):
        x = -0.33 + i * 0.22
        o.append(put(col, f"icon_seo_bar_{i+1:02d}",
                     I.prism_mesh(f"seo_bar_{i+1:02d}", I.rect_pts(0.16, h), 0.16),
                     m[c], (x, 0.0, -0.3925 + h / 2)))
    o.append(put(col, "icon_seo_arrow",
                 I.prism_mesh("seo_arrow", I.arrow_pts(0.86, 0.035, 0.20, 0.115), 0.075),
                 m["mat_cobalt"], (0.0, -0.135, 0.10), (0.0, D(-38.0), 0.0)))
    return o

# ------------------------------------------------------------------ 4. mobile
def build_mobile(col, m):
    o = []
    o.append(put(col, "icon_mobile_body", I.prism_mesh("mob_body", I.rect_pts(0.46, 0.88), 0.11),
                 m["mat_charcoal"], (0.0, 0.0, 0.0)))
    o.append(put(col, "icon_mobile_screen", I.prism_mesh("mob_screen", I.rect_pts(0.36, 0.72), 0.03),
                 m["mat_cream"], (0.0, -0.07, 0.02)))
    o.append(put(col, "icon_mobile_accent", I.prism_mesh("mob_accent", I.rect_pts(0.24, 0.055), 0.02),
                 m["mat_cobalt"], (0.0, -0.095, 0.25)))
    o.append(put(col, "icon_mobile_bar_01", I.prism_mesh("mob_bar_01", I.rect_pts(0.17, 0.04), 0.018),
                 m["mat_stone"], (-0.025, -0.094, 0.13)))
    o.append(put(col, "icon_mobile_bar_02", I.prism_mesh("mob_bar_02", I.rect_pts(0.12, 0.04), 0.018),
                 m["mat_stone"], (-0.05, -0.094, 0.04)))
    return o

# ------------------------------------------------------------------ 5. cro
def build_cro(col, m):
    prof = []
    for k in range(8):                       # cone: wide mouth down to the throat
        s = k / 7
        prof.append((0.42 + (0.13 - 0.42) * s, 0.20 + (-0.10 - 0.20) * s))
    for k in range(1, 4):                    # straight stem
        s = k / 3
        prof.append((0.13, -0.10 + (-0.34 + 0.10) * s))
    funnel = I.revolve_mesh("cro_funnel", prof, seg=28)
    ob = L.new_object("icon_cro_funnel", funnel, col, m["mat_cream"])
    sm = ob.modifiers.new("solidify", "SOLIDIFY")
    sm.thickness, sm.offset = 0.026, 0.0
    o = [ob]
    o.append(put(col, "icon_cro_rim", I.torus_mesh("cro_rim", 0.42, 0.022, 32, 8),
                 m["mat_charcoal"], (0.0, 0.0, 0.20)))
    o.append(put(col, "icon_cro_collar", I.torus_mesh("cro_collar", 0.13, 0.019, 22, 8),
                 m["mat_stone"], (0.0, 0.0, -0.33)))
    o.append(put(col, "icon_cro_sphere", L.sphere_mesh("cro_sphere", 0.105, 24, 12),
                 m["mat_cobalt"], (0.0, 0.0, -0.50)))
    return o

# ------------------------------------------------------------------ 6. support
def build_support(col, m):
    o = []
    o.append(put(col, "icon_support_shield", I.prism_mesh("sup_shield", I.shield_pts(0.72, 0.88), 0.13),
                 m["mat_cream"], (0.0, 0.0, 0.0)))
    o.append(put(col, "icon_support_face", I.prism_mesh("sup_face", I.shield_pts(0.56, 0.68), 0.04),
                 m["mat_stone"], (0.0, -0.085, 0.0)))
    emblem = L.chain_link_mesh("sup_emblem", 0.115, 0.15, 0.036,
                               n_semi=10, n_straight=3, n_ring=12)
    o.append(put(col, "icon_support_emblem", emblem, m["mat_cobalt"],
                 (0.0, -0.141, 0.02), (D(90.0), D(-18.0), 0.0)))
    return o

# ------------------------------------------------------------------ runner
ICONS = [
    ("icon_01_web_design",   "Website Design & Development", build_web),
    ("icon_02_brand_identity", "Brand Identity",             build_brand),
    ("icon_03_seo_performance", "SEO & Performance",         build_seo),
    ("icon_04_mobile_first", "Mobile-First",                 build_mobile),
    ("icon_05_conversion",   "Conversion Rate Optimization", build_cro),
    ("icon_06_support",      "Maintenance & Support",        build_support),
]

def run(indices, render=True):
    out = []
    for idx in indices:
        stem, label, builder = ICONS[idx]
        L.reset_scene()
        mats = L.brand_materials()
        col = L.get_collection("lynkwell_icon")
        objs = builder(col, mats)
        scale, size = I.normalise(objs)
        for ob in objs:
            I.add_icon_bevel(ob)
        seam = I.build_idle(objs)
        tris, per = L.tri_count(objs)
        I.build_rig()
        glb, blend, kb = I.export_icon(objs, stem)
        png = f"{I.ROOT}/previews/{stem}.png"
        secs = 0.0
        if render:
            bpy.context.scene.render.filepath = png
            t0 = time.time()
            I.run_op(bpy.ops.render.render, write_still=True)
            secs = round(time.time() - t0, 1)
        out.append({"stem": stem, "label": label, "objects": len(objs),
                    "tris": tris, "glb_kb": kb, "norm_scale": round(scale, 3),
                    "size": size, "idle_seam": seam, "render_s": secs,
                    "materials": sorted({mm.name for ob in objs for mm in ob.data.materials})})
    return out
