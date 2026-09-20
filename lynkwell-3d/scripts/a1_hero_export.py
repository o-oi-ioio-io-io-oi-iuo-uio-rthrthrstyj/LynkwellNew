"""Asset 1 - save .blend and export the Draco-compressed .glb."""
import bpy, os, sys

ROOT = "/Users/jackdworkin/Claude Code Projects/lynkwell-3d"
sc   = bpy.context.scene
hero = bpy.data.collections["lynkwell_hero"]
assets = list(hero.objects)

# unmute the NLA tracks so the exporter sees them
for ob in assets:
    if ob.animation_data:
        for t in ob.animation_data.nla_tracks:
            t.mute = False

for ob in bpy.context.view_layer.objects:          # data-API deselect (no operator context)
    ob.select_set(False)
for ob in assets:
    ob.select_set(True)
bpy.context.view_layer.objects.active = assets[0]

blend = os.path.join(ROOT, "blend", "hero_link_network.blend")
glb   = os.path.join(ROOT, "export", "hero_link_network.glb")

bpy.ops.export_scene.gltf(
    filepath=glb,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_cameras=False,
    export_lights=False,
    export_materials="EXPORT",
    export_extras=False,
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
    export_animations=True,
    export_animation_mode="NLA_TRACKS",
    export_force_sampling=True,
    export_optimize_animation_size=True,
    export_frame_range=False,
    export_nla_strips=True,
)

# Unmuting the tracks let Blender write evaluated (idle) values back onto the
# objects, so the rest pose MUST be restored from the stash before saving.
for ob in assets:
    if ob.animation_data:
        for t in ob.animation_data.nla_tracks:
            t.mute = True
sc.frame_set(120)
import sys, importlib
sys.path.insert(0, ROOT + "/scripts")
import lynkwell_lib as L; importlib.reload(L)
L.restore_base(assets)
bpy.ops.wm.save_as_mainfile(filepath=blend)

result = {"blend": blend, "blend_kb": round(os.path.getsize(blend) / 1024, 1),
          "glb": glb, "glb_kb": round(os.path.getsize(glb) / 1024, 1)}
