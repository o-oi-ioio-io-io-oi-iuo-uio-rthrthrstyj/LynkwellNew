"""Asset 1 - Hero 'Link Network'. Geometry, materials, layout, preview rig."""
import bpy, math, sys, importlib
from mathutils import Vector

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L
importlib.reload(L)

D = math.radians

# ---- link proportions (metres) -------------------------------------------
A, E, R = 0.098, 0.170, 0.032          # outer 0.430 long x 0.260 wide
PITCH   = 0.280                        # centre-to-centre along the chain
STEP    = 33.0                         # degrees of arc per link
N_LINK  = 7
RC      = PITCH / D(STEP)              # arc radius ~0.486
START   = -(N_LINK - 1) * STEP / 2.0   # -99 deg .. +99 deg, opening faces -X

LINK_MATS = ["mat_stone", "mat_cream", "mat_charcoal", "mat_cream",
             "mat_cobalt", "mat_stone", "mat_charcoal"]   # index 4 = the one cobalt link

NODES = [  # name, radius, position, material
    ("hero_node_01", 0.058, Vector((-0.335, -0.055,  0.075)), "mat_cream"),
    ("hero_node_02", 0.044, Vector((-0.615, -0.115, -0.185)), "mat_stone"),
    ("hero_node_03", 0.034, Vector((-0.470, -0.020,  0.400)), "mat_charcoal"),
]
ROD_R = 0.011

# ---- scene ----------------------------------------------------------------
sc = L.reset_scene()
mats = L.brand_materials()
hero = L.get_collection("lynkwell_hero")
rig  = L.get_collection("preview_rig")

links = []
for i in range(N_LINK):
    theta = START + i * STEP
    psi   = 0.0 if i % 2 == 0 else 90.0
    name  = f"hero_link_{i+1:02d}"
    me    = L.chain_link_mesh(name + "_mesh", A, E, R)
    ob    = L.new_object(name, me, hero, mats[LINK_MATS[i]])
    ob.location = Vector((RC * math.cos(D(theta)), 0.0, RC * math.sin(D(theta))))
    ob.rotation_euler = (D(90.0 + psi), -D(theta + 90.0), 0.0)
    links.append(ob)

nodes = []
for name, rad, pos, mat in NODES:
    ob = L.new_object(name, L.sphere_mesh(name + "_mesh", rad), hero, mats[mat])
    ob.location = pos
    nodes.append(ob)

def make_rod(name, p0, p1):
    d = p1 - p0
    me = L.rod_mesh(name + "_mesh", ROD_R, d.length)
    ob = L.new_object(name, me, hero, mats["mat_stone"])
    ob.location = (p0 + p1) * 0.5
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    L.add_bevel(ob)
    return ob

rods = [
    make_rod("hero_rod_01", links[6].location.copy(), nodes[2].location.copy()),
    make_rod("hero_rod_02", nodes[2].location.copy(), nodes[0].location.copy()),
    make_rod("hero_rod_03", nodes[0].location.copy(), nodes[1].location.copy()),
    make_rod("hero_rod_04", nodes[0].location.copy(), links[0].location.copy()),
]

assets = links + nodes + rods
bpy.context.view_layer.update()

# ---- interlock sanity check: min centreline gap between neighbouring links
def centreline(ob, n=96):
    mw, out = ob.matrix_world, []
    me = ob.data
    for k in range(n):
        v = me.vertices[int(k * len(me.vertices) / n)]
        out.append(mw @ v.co)
    return out

gaps = []
for i in range(N_LINK - 1):
    pa, pb = centreline(links[i]), centreline(links[i + 1])
    gaps.append(round(min((x - y).length for x in pa for y in pb), 4))

offset, size = L.recentre(assets)
total, per = L.tri_count(assets)

result = {
    "arc_radius": round(RC, 4),
    "link_outer_LxW": [round(E + 2 * A + 2 * R, 3), round(2 * A + 2 * R, 3)],
    "neighbour_surface_gaps": gaps,          # must stay > 0 (2*R = 0.064 centreline min)
    "tube_diameter": 2 * R,
    "recentre_offset": [round(v, 4) for v in offset],
    "bbox_size": [round(v, 3) for v in size],
    "objects": len(assets),
    "tris_total": total,
    "tris_per_object": per,
}
