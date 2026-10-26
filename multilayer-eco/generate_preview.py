"""
MultilayerEco — Preview com camadas em escada diagonal.
Camada mais alta: canto superior-esquerdo
Camada do meio: centro
Camada mais baixa: canto inferior-direito
"""
import sys, math
sys.path.insert(0, '/sessions/inspiring-zen-thompson/mnt/APP ECOSSISTEMA /multilayer-eco')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from core.models import Project, RELATION_TYPE_STYLES
from core.graph_engine import GraphEngine

# ─── BUILD PROJECT ──────────────────────────────────────────────────
project = Project(name='Ecossistema IA — NYT vs OpenAI')
l_con = project.add_layer('Conhecimento',   '#3498DB')
l_inf = project.add_layer('Infraestrutura', '#27AE60')
l_neg = project.add_layer('Negócios',       '#E74C3C')

nyt  = project.add_actor('New York Times', 'Mídia',     [l_con.id, l_neg.id])
oai  = project.add_actor('OpenAI',         'Empresa',   [l_con.id, l_inf.id, l_neg.id])
ms   = project.add_actor('Microsoft',      'Empresa',   [l_inf.id, l_neg.id])
cc   = project.add_actor('Common Crawl',   'Plataforma',[l_con.id])
nv   = project.add_actor('Nvidia',         'Empresa',   [l_inf.id])
cgpt = project.add_actor('ChatGPT',        'Tecnologia',[l_neg.id])
cop  = project.add_actor('MS Copilot',     'Tecnologia',[l_neg.id])
wc   = project.add_actor('Wirecutter',     'Mídia',     [l_con.id, l_neg.id])
gbot = project.add_actor('GPTBot',         'Tecnologia',[l_con.id])
trib = project.add_actor('Tribunal SDNY',  'Regulador', [l_neg.id])
nma  = project.add_actor('News Alliance',  'ONG',       [l_neg.id])
ag   = project.add_actor('Authors Guild',  'ONG',       [l_neg.id])
goog = project.add_actor('Google',         'Empresa',   [l_con.id, l_inf.id, l_neg.id])
aws  = project.add_actor('Amazon AWS',     'Empresa',   [l_inf.id])

for s,t,l,rt,d in [
    (nyt,oai,l_con,'extração','source_to_target'),
    (cc,oai,l_con,'fornecimento','source_to_target'),
    (gbot,nyt,l_con,'extração','source_to_target'),
    (wc,nyt,l_con,'cooperação','bidirectional'),
    (cc,goog,l_con,'fornecimento','source_to_target'),
    (oai,goog,l_con,'competição','bidirectional'),
    (ms,oai,l_inf,'investimento','source_to_target'),
    (nv,ms,l_inf,'fornecimento','source_to_target'),
    (nv,goog,l_inf,'fornecimento','source_to_target'),
    (aws,oai,l_inf,'competição','bidirectional'),
    (ms,goog,l_inf,'competição','bidirectional'),
    (cgpt,nyt,l_neg,'competição','bidirectional'),
    (cop,nyt,l_neg,'competição','bidirectional'),
    (oai,cgpt,l_neg,'integração','source_to_target'),
    (nyt,trib,l_neg,'regulação','source_to_target'),
    (nma,nyt,l_neg,'cooperação','source_to_target'),
    (ag,oai,l_neg,'conflito','source_to_target'),
    (ms,cop,l_neg,'integração','source_to_target'),
    (wc,cgpt,l_neg,'dependência','source_to_target'),
    (goog,oai,l_neg,'competição','bidirectional'),
]:
    project.add_relationship(s.id,t.id,l.id,rt,d)

for s,t,sl,tl,rt in [
    (oai,oai,l_con,l_inf,'integração'),
    (oai,oai,l_inf,l_neg,'integração'),
    (nyt,nyt,l_con,l_neg,'dependência'),
    (ms,ms,l_inf,l_neg,'integração'),
    (goog,goog,l_con,l_neg,'integração'),
    (wc,wc,l_con,l_neg,'dependência'),
]:
    project.add_relationship(s.id,t.id,rel_type=rt,direction='source_to_target',
                            source_layer_id=sl.id,target_layer_id=tl.id)

# ─── MANUAL POSITIONS ───────────────────────────────────────────────
# Each layer's nodes are placed inside [0..10] x [0..10]
pos = {
    # Conhecimento
    (nyt.id,  l_con.id): (2.0, 6.0),
    (oai.id,  l_con.id): (5.5, 5.5),
    (cc.id,   l_con.id): (8.0, 8.0),
    (wc.id,   l_con.id): (1.5, 3.0),
    (gbot.id, l_con.id): (4.0, 8.5),
    (goog.id, l_con.id): (8.0, 2.5),
    # Infraestrutura
    (oai.id,  l_inf.id): (5.0, 6.0),
    (ms.id,   l_inf.id): (2.5, 3.5),
    (nv.id,   l_inf.id): (2.0, 7.5),
    (goog.id, l_inf.id): (7.5, 2.5),
    (aws.id,  l_inf.id): (8.0, 7.0),
    # Negócios
    (nyt.id,  l_neg.id): (2.0, 5.5),
    (oai.id,  l_neg.id): (5.5, 5.0),
    (ms.id,   l_neg.id): (5.0, 8.0),
    (cgpt.id, l_neg.id): (4.0, 2.5),
    (cop.id,  l_neg.id): (3.0, 8.0),
    (wc.id,   l_neg.id): (1.5, 2.5),
    (trib.id, l_neg.id): (1.5, 8.5),
    (nma.id,  l_neg.id): (2.8, 8.5),
    (ag.id,   l_neg.id): (8.0, 7.5),
    (goog.id, l_neg.id): (8.0, 3.0),
}
for (aid, lid), (x, y) in pos.items():
    if aid in project.actors:
        project.actors[aid].positions[lid] = (x, y)

# ─── LAYER GEOMETRY (staircase diagonal) ────────────────────────────
# Each layer is a parallelogram defined by (ox, oy) origin in 3D,
# width W along X axis and depth D along Y axis with a skew in Z.
#
# Layout: top-layer at top-left, mid at center, bottom at bottom-right
# In 3D (X, Y, Z):  X = left-right, Y = depth, Z = up-down
#
# We'll project to 2D with a simple oblique projection:
#   screen_x = X + Y * cos(angle)
#   screen_y = Z + Y * sin(angle)

ANGLE  = math.radians(30)   # oblique angle
COS_A  = math.cos(ANGLE)
SIN_A  = math.sin(ANGLE)
W      = 9.0    # plane width  (X axis)
D      = 9.0    # plane depth  (Y axis)

# Staircase offsets: each layer displaced diagonally
# Layer 2 (top/Conhecimento):   X-offset=0,  Z-offset=14
# Layer 1 (mid/Infraestrutura): X-offset=7,  Z-offset=7
# Layer 0 (bot/Negócios):       X-offset=14, Z-offset=0
STAIR_STEP = 7.0

layer_offsets = {
    l_con.id: (0 * STAIR_STEP, 2 * STAIR_STEP),   # (X_off, Z_off)
    l_inf.id: (1 * STAIR_STEP, 1 * STAIR_STEP),
    l_neg.id: (2 * STAIR_STEP, 0 * STAIR_STEP),
}
layer_colors = {
    l_con.id: '#3498DB',
    l_inf.id: '#27AE60',
    l_neg.id: '#E74C3C',
}
layer_labels = {
    l_con.id: 'Conhecimento',
    l_inf.id: 'Infraestrutura',
    l_neg.id: 'Negócios',
}
layer_ids_ordered = [l_con.id, l_inf.id, l_neg.id]  # top to bottom (for Z-order)

def to_screen(X, Y, Z, X_off, Z_off):
    """Oblique projection: map 3D coords to 2D screen."""
    sx = (X + X_off) + (Y) * COS_A
    sy = (Z + Z_off) + (Y) * SIN_A
    return sx, sy

def node_screen(actor_id, layer_id):
    """Get the screen (2D) position of a node."""
    p = pos.get((actor_id, layer_id))
    if p is None:
        return None
    x, y = p  # [0..10]
    # Map [0..10] to plane coords [0..W] x [0..D]
    lx = x / 10.0 * W
    ly = y / 10.0 * D
    X_off, Z_off = layer_offsets[layer_id]
    sx, sy = to_screen(lx, ly, 0, X_off, Z_off)
    return sx, sy

# ─── RENDER ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(17, 13), facecolor='white')
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor('white')

import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrow, FancyArrowPatch
from matplotlib.collections import LineCollection

# Draw from back to front (top layer first since it's in upper-left)
for lid in layer_ids_ordered:
    c = layer_colors[lid]
    X_off, Z_off = layer_offsets[lid]

    # ── Plane fill ──
    # Four corners: (0,0),(W,0),(W,D),(0,D) in layer space
    corners_3d = [(0,0),(W,0),(W,D),(0,D)]
    corners_2d = [to_screen(cx, cy, 0, X_off, Z_off) for cx, cy in corners_3d]
    xs = [p[0] for p in corners_2d] + [corners_2d[0][0]]
    ys = [p[1] for p in corners_2d] + [corners_2d[0][1]]
    # Fill with very light color
    fill_c = plt.matplotlib.colors.to_rgba(c, alpha=0.10)
    ax.fill(xs[:-1], ys[:-1], color=c, alpha=0.10, zorder=1)
    # Border
    ax.plot(xs, ys, color=c, alpha=0.55, linewidth=2.0, zorder=2)

    # ── Intra-layer edges ──
    for rel in project.relationships:
        if rel.is_inter_layer or rel.layer_id != lid:
            continue
        sp = node_screen(rel.source_id, lid)
        tp = node_screen(rel.target_id, lid)
        if sp is None or tp is None:
            continue
        si = RELATION_TYPE_STYLES.get(rel.rel_type, RELATION_TYPE_STYLES['outro'])
        col = si['color']
        ls = '-' if si['style']=='solid' else ('--' if si['style']=='dash' else ':')
        lw = si['width'] * 0.65
        ax.plot([sp[0],tp[0]], [sp[1],tp[1]], color=col, alpha=0.55,
                linewidth=lw, linestyle=ls, zorder=3)
        # Directed arrow marker
        if rel.direction in ('source_to_target','target_to_source'):
            fx, fy = (sp,tp) if rel.direction=='source_to_target' else (tp,sp)
            tx, ty = (tp,sp) if rel.direction=='source_to_target' else (sp,tp)
            mx = fx[0] + 0.72*(tx[0]-fx[0])
            my = fx[1] + 0.72*(tx[1]-fx[1])
            dx = tx[0]-fx[0]; dy = tx[1]-fy[1]
            length = math.sqrt(dx**2+dy**2)
            if length > 0.01:
                ax.annotate('', xy=(mx,my),
                           xytext=(mx - dx/length*0.4, my - dy/length*0.4),
                           arrowprops=dict(arrowstyle='->', color=col,
                                         lw=lw, mutation_scale=10),
                           zorder=4)

    # ── Nodes ──
    actors_in_layer = project.get_actors_in_layer(lid)
    for actor in actors_in_layer:
        sp = node_screen(actor.id, lid)
        if sp is None:
            continue
        # Dark circle
        circle = plt.Circle(sp, 0.28, color='#2C3E50', zorder=7, linewidth=1.2)
        circle_border = plt.Circle(sp, 0.28, fill=False, color='white',
                                   linewidth=1.2, zorder=8)
        ax.add_patch(circle)
        ax.add_patch(circle_border)
        # Label with background
        ax.text(sp[0]+0.35, sp[1]+0.15, actor.name,
               fontsize=7.0, color='#1A252F', va='bottom', ha='left', zorder=9,
               fontweight='semibold',
               bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                        edgecolor='none', alpha=0.72))

    # ── Layer label (right side of plane) ──
    # Place at far-right of the plane
    label_x, label_y = to_screen(W + 0.3, D/2, 0, X_off, Z_off)
    ax.text(label_x + 0.3, label_y, layer_labels[lid],
           fontsize=13, fontweight='bold', color=c, va='center', ha='left',
           zorder=10,
           bbox=dict(boxstyle='round,pad=0.35', facecolor='white',
                    edgecolor=c, linewidth=1.5, alpha=0.92))

# ── Inter-layer / identity links ──
for actor in project.actors.values():
    if len(actor.layers) < 2:
        continue
    # Draw connecting lines between all layer instances of this actor
    layer_positions = []
    for lid in [l_con.id, l_inf.id, l_neg.id]:
        if lid in actor.layers:
            sp = node_screen(actor.id, lid)
            if sp:
                layer_positions.append(sp)
    for i in range(len(layer_positions)-1):
        p1, p2 = layer_positions[i], layer_positions[i+1]
        ax.plot([p1[0],p2[0]], [p1[1],p2[1]],
               color='#2C3E50', alpha=0.18, linewidth=0.9,
               linestyle=(0,(4,5)), zorder=0)

# ─── LEGEND ─────────────────────────────────────────────────────────
legend_items = [
    ('cooperação',       '#27AE60', '-',  2.0),
    ('competição',       '#E74C3C', '--', 2.0),
    ('dependência',      '#F39C12', '-',  2.0),
    ('fornecimento',     '#3498DB', '-',  2.0),
    ('extração',         '#C0392B', '-',  2.5),
    ('regulação',        '#9B59B6', ':',  2.0),
    ('investimento',     '#2ECC71', '-',  2.5),
    ('conflito',         '#E74C3C', '--', 2.5),
    ('integração',       '#16A085', '-',  2.0),
    ('link inter-camada','#2C3E50', ':',  1.0),
]
handles = [
    plt.Line2D([0],[0], color=c, linewidth=lw, linestyle=ls, label=lb)
    for lb,c,ls,lw in legend_items
]
leg = ax.legend(handles=handles, loc='upper right', fontsize=8,
               framealpha=0.93, edgecolor='#D5D8DC', fancybox=True,
               ncol=2, title='Tipos de Relação',
               title_fontsize=8.5)
leg.get_frame().set_linewidth(1.0)

# ─── TITLE ──────────────────────────────────────────────────────────
ax.set_title('MultilayerEco — Ecossistema de IA Multinível\n'
             'Caso Ilustrativo: NYT vs OpenAI  |  3 camadas · 14 atores · 26 relações',
             fontsize=14, fontweight='bold', color='#2C3E50', pad=15)

# Auto-set limits with padding
all_pts = []
for lid in layer_ids_ordered:
    for aid in project.actors:
        sp = node_screen(aid, lid)
        if sp:
            all_pts.append(sp)
xs = [p[0] for p in all_pts]
ys = [p[1] for p in all_pts]
pad = 2.5
ax.set_xlim(min(xs)-pad, max(xs)+pad+4)  # extra right for labels
ax.set_ylim(min(ys)-pad, max(ys)+pad)

plt.tight_layout(pad=2.0)
out = '/sessions/inspiring-zen-thompson/mnt/APP ECOSSISTEMA /multilayer-eco/preview_3d.png'
fig.savefig(out, dpi=180, bbox_inches='tight', facecolor='white')
print(f'OK: {out}')
