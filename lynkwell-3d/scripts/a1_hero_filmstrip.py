"""Asset 1 - render an 'assemble' filmstrip so the scroll timeline can be judged."""
import bpy, numpy as np

sc = bpy.context.scene
TMP = "/private/tmp/claude-501/-Users-jackdworkin-Claude-Code-Projects/e918487a-fd73-4c4e-91af-831a93eaa44e/scratchpad"
hero = bpy.data.collections["lynkwell_hero"]

for ob in hero.objects:
    for t in ob.animation_data.nla_tracks:
        t.mute = (t.name != "assemble")

rx, ry, sm = sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples
sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = 430, 322, 28

FRAMES = [0, 40, 75, 120]
tiles = []
for f in FRAMES:
    sc.frame_set(f)
    sc.render.filepath = f"{TMP}/asm_{f:03d}.png"
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(f"{TMP}/asm_{f:03d}.png", check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    a[:4, :, :3] = a[-4:, :, :3] = a[:, :3, :3] = a[:, -3:, :3] = 0.86   # hairline gutters
    tiles.append(a)

strip = np.concatenate(tiles, axis=1)
H, W = strip.shape[:2]
out = bpy.data.images.new("assemble_strip", width=W, height=H, alpha=False)
out.pixels = strip.ravel().tolist()
out.filepath_raw = f"{TMP}/assemble_strip.png"
out.file_format = "PNG"
out.save()
bpy.data.images.remove(out)

sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = rx, ry, sm
for ob in hero.objects:
    for t in ob.animation_data.nla_tracks:
        t.mute = True
sc.frame_set(120)
import sys, importlib
sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as LL; importlib.reload(LL)
LL.restore_base(list(hero.objects))

result = {"frames": FRAMES, "strip": f"{TMP}/assemble_strip.png", "size": [W, H]}
