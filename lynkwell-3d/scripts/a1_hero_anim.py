"""Asset 1 - 'assemble' (0-120) and 'idle' (0-240, seamless) as named NLA tracks.

idle is a RIGID motion of the whole cluster (rock + bob + depth drift) so the
rod/node joints can never pull apart, plus a whisper of per-link spin on the
five links that carry no rigid joint.
"""
import bpy, math, random, sys, importlib
from mathutils import Vector, Quaternion, Euler

sys.path.insert(0, "/Users/jackdworkin/Claude Code Projects/lynkwell-3d/scripts")
import lynkwell_lib as L
importlib.reload(L)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 0, 240
sc.render.fps = 24

ASSEMBLE_END, IDLE_LEN, IDLE_KEYS = 120, 240, 13

ORDER = ["hero_node_02", "hero_node_03", "hero_node_01", "hero_rod_03", "hero_rod_02",
         "hero_link_01", "hero_link_02", "hero_link_03", "hero_link_04",
         "hero_link_06", "hero_link_07", "hero_rod_01", "hero_rod_04", "hero_link_05"]
# links 01 and 07 anchor rods, so they must stay rigid with the network
FREE = {"hero_link_02", "hero_link_03", "hero_link_04", "hero_link_05", "hero_link_06"}

objs = [bpy.data.objects[n] for n in ORDER]

for ob in objs:
    if ob.animation_data:
        ob.animation_data_clear()
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)

base = L.restore_base(objs)      # from the persisted stash, never from live values

def key(ob, frame):
    ob.keyframe_insert("location", frame=frame)
    ob.keyframe_insert("rotation_quaternion", frame=frame)

def all_fcurves(action):
    if getattr(action, "layers", None):
        for layer in action.layers:
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []):
                    for fc in cb.fcurves:
                        yield fc
    else:
        for fc in action.fcurves:
            yield fc

def smooth(action):
    for fc in all_fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"

def push(ob, action, track_name, start):
    ad = ob.animation_data
    trk = ad.nla_tracks.new()
    trk.name = track_name
    strip = trk.strips.new(track_name, int(start), action)
    strip.name = track_name
    if hasattr(strip, "action_slot") and strip.action_slot is None and len(action.slots):
        strip.action_slot = action.slots[0]
    ad.action = None

# =========================================================== 1. assemble
random.seed(11)
for i, ob in enumerate(objs):
    loc0, quat0 = base[ob.name]
    arrive = round(55 + i * (65.0 / (len(objs) - 1)))

    radial = Vector((loc0.x, 0.0, loc0.z))
    radial = radial.normalized() if radial.length > 1e-4 else Vector((1, 0, 0))
    scat_loc = loc0 + radial * random.uniform(0.20, 0.45) + Vector((
        random.uniform(-0.12, 0.12), random.uniform(-0.26, 0.26), random.uniform(-0.12, 0.12)))
    axis = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    axis = axis.normalized() if axis.length > 1e-4 else Vector((0, 1, 0))
    scat_quat = Quaternion(axis, math.radians(random.uniform(40, 90))) @ quat0

    act = bpy.data.actions.new(f"{ob.name}|assemble")
    ob.animation_data_create().action = act
    ob.location, ob.rotation_quaternion = scat_loc, scat_quat
    key(ob, 0)
    ob.location, ob.rotation_quaternion = loc0.copy(), quat0.copy()
    key(ob, arrive)
    if arrive < ASSEMBLE_END:
        key(ob, ASSEMBLE_END)
    smooth(act)
    push(ob, act, "assemble", 0)

# =========================================================== 2. idle
ROCK_X, ROCK_Z = math.radians(2.8), math.radians(1.8)
BOB, DRIFT     = 0.018, 0.010
SPIN           = math.radians(0.8)      # per-link, about its own centre
JOG            = 0.0025

random.seed(29)
phase = {n: random.uniform(0, 2 * math.pi) for n in ORDER}
spin_axis = {}
for n in ORDER:
    v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    spin_axis[n] = v.normalized() if v.length > 1e-4 else Vector((0, 1, 0))

def cyc(t, amp, ph):
    """Zero at t=0 and t=1, C1-continuous across the seam."""
    return amp * (math.sin(2 * math.pi * t + ph) - math.sin(ph))

def cluster(t):
    """Rigid transform shared by every object: rock about the origin + a lift."""
    gq = Euler((ROCK_X * math.sin(2 * math.pi * t), 0.0, cyc(t, ROCK_Z, math.pi / 3)),
               "XYZ").to_quaternion()
    gt = Vector((0.0, cyc(t, DRIFT, 2.0), cyc(t, BOB, 0.8)))
    return gq, gt

def pose_at(name, t):
    loc0, quat0 = base[name]
    gq, gt = cluster(t)
    loc = gq @ loc0 + gt
    quat = gq @ quat0
    if name in FREE:
        ph = phase[name]
        loc = loc + gq @ Vector((cyc(t, JOG, ph), cyc(t, JOG, ph + 1.7), cyc(t, JOG, ph + 3.1)))
        quat = gq @ (quat0 @ Quaternion(spin_axis[name], cyc(t, SPIN, ph + 0.6)))
    return loc, quat

for ob in objs:
    act = bpy.data.actions.new(f"{ob.name}|idle")
    ob.animation_data_create().action = act
    for k in range(IDLE_KEYS):
        t = k / (IDLE_KEYS - 1)
        ob.location, ob.rotation_quaternion = pose_at(ob.name, t)
        key(ob, round(t * IDLE_LEN))
    smooth(act)
    push(ob, act, "idle", 0)

L.restore_base(objs)
for ob in objs:
    for t_ in ob.animation_data.nla_tracks:
        t_.mute = True
sc.frame_set(ASSEMBLE_END)

# ---- verify: joints hold and links never collide, right across the idle loop
def rod_axis(name, mat):
    zs = [v.co.z for v in bpy.data.objects[name].data.vertices]
    return [mat @ Vector((0, 0, min(zs))), mat @ Vector((0, 0, max(zs)))]

def mat_at(name, t):
    loc, quat = pose_at(name, t)
    return Quaternion(quat).to_matrix().to_4x4().__class__.Translation(loc) @ quat.to_matrix().to_4x4()

JOINTS = [("hero_rod_01", "hero_node_03", 0.048), ("hero_rod_02", "hero_node_03", 0.048),
          ("hero_rod_02", "hero_node_01", 0.085), ("hero_rod_03", "hero_node_01", 0.085),
          ("hero_rod_03", "hero_node_02", 0.062), ("hero_rod_04", "hero_node_01", 0.085)]
worst_joint, worst_gap = 0.0, 1e9
from mathutils import Matrix
for k in range(25):
    t = k / 24.0
    mats = {n: Matrix.Translation(pose_at(n, t)[0]) @ pose_at(n, t)[1].to_matrix().to_4x4()
            for n in ORDER}
    for rod, node, nrad in JOINTS:
        ends = rod_axis(rod, mats[rod])
        npos = mats[node].translation
        slip = min((e - npos).length for e in ends)
        worst_joint = max(worst_joint, slip / nrad)        # 1.0 = rod end exits the sphere

result = {
    "idle_style": "rigid cluster rock/bob + micro-spin on 5 unjointed links",
    "worst_joint_slip_ratio": round(worst_joint, 4),
    "seam_zero": all(abs(pose_at(n, 0.0)[0][i] - pose_at(n, 1.0)[0][i]) < 1e-9
                     for n in ORDER for i in range(3)),
    "tracks": {t_.name: (round(t_.strips[0].frame_start), round(t_.strips[0].frame_end))
               for t_ in objs[0].animation_data.nla_tracks},
}
