# %%
from itertools import cycle
from glob import glob
from typing import Union, Tuple, List
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Arrow, Rectangle, Polygon, Circle
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pandas.core.window import rolling
from pycocotools import coco
import tensorflow as tf
from tensorflow.keras.layers import Layer
from tensorflow.keras.losses import Loss
from tensorflow.keras.utils import load_img
import pprint as pp

from src.utils.box_cutter import BoundingBox_Processor
from src.utils.classes import CategoricalDataGen
from src.utils.data_worker import LabelWorker
from src.utils.funcs import *

# %%
# %load_ext autoreload

# %%
# %autoreload 2
# %aimport src.utils.funcs
# %aimport src.utils.box_cutter
# %aimport src.utils.classes
# %aimport src.utils.data_worker

# %%
pp.PrettyPrinter(indent=4)

# %%
color = cycle(["orange", "crimson", "tomato",
               "springgreen", "aquamarine", 
               "fuchsia", "deepskyblue", 
               "mediumorchid", "gold"])
images = sorted(glob("./data/images/train/*"))

# %%
data = init_COCO("./data/", ['train', 'val', 'test'])
box_cutter = BoundingBox_Processor()

# %%
labeler = LabelWorker(data_name='train',
                      coco_obj=data,
                      image_path='./data/images/',
                      input_size=(1440, 1920),
                      target_size=(384, 512))

# %%
num_anchors = 9
labels = labeler.label_list()[:16]
anchors = stack_anchors(generate_anchors(labels, boxes_per_cell=num_anchors, random_state=42))
label_corners = get_corners(labels)
anchor_corners = get_corners(anchors)
label_edges = get_edges(label_corners)
anchor_edges = get_edges(anchor_corners)
print(f"labels shape: {labels.shape}")
print(f"label_corners shape: {label_corners.shape}")
print(f"label_edges shape: {label_edges.shape}")
print(f"anchors shape: {anchors.shape}")
print(f"anchor_corners shape: {anchor_corners.shape}")
print(f"anchor_edges shape: {anchor_edges.shape}")

# %%
anchor_edges[0, an::108].shape

# %%
old_corners = box_cutter.get_corners(labels)[0]
old_anchors = box_cutter.get_corners(anchors)[0]
print(f"old_corners: {old_corners.shape}")
print(f"old_anchros: {old_anchors.shape}")
old_intersections = box_cutter.rolling_intersection(old_corners, old_anchors)[0]
old_intersections.shape

# %%
an = 9 * 3 + 2 + 108
bb = 5

# %%
x_points = construct_intersection_vertices(labels, anchors, num_pumps=num_anchors)
print(f"x_points: {x_points.shape}")

# %%
union = union_area(label_corners, anchor_corners, areas, num_pumps=num_anchors)
print(f"union: {union.shape}, {union.dtype}")
print(f"union:\n{union[0, bb, an::108]}")

# %%
intersection = intersection_area(x_points)
print(f"areas: {intersection.shape}, {intersection.dtype}")
print(f"areas:\n{intersection[0, bb, an::108]}")

# %%
iou = intersection / union
print(f"IoU: {iou.shape}, {iou.dtype}")
print(f"IoU:\n{iou[0, bb, an::108]}")

# %%
an = 9 * 3 + 2
bb = 5

fig, ax = plt.subplots(figsize=(8, 6))
ax.set(
        ylim=[0, 384],
        xlim=[0, 512],
        xticks=list(range(0, 512,int(np.ceil(512/12)))),
        yticks=list(range(0, 384, int(np.ceil(384/9)))),
        )
lines = []
verts = []
for i in range(num_anchors * 24):
    point = tf.reshape(x_points[0, bb, an::108], [num_anchors * 24, 2])[i]
    if point[0] == 0:
        continue
    verts.append(Circle(point, radius=2, color="tomato", zorder=10))
for i in range(1, 12, 1):
    line = i * 512/12
    lines.append([(line, 0), (line, 384)])
for i in range(1, 9, 1):
    line = i * 384/9
    lines.append([(0, line), (512, line)])
grid_lines = mpl.collections.LineCollection(lines, colors='black', lw=1, alpha=1, zorder=200)
ax.add_collection(grid_lines)
ax.add_collection(mpl.collections.LineCollection(label_edges[0, bb]))
ax.add_collection(mpl.collections.LineCollection(anchor_edges[0, an::108].numpy().reshape(num_anchors * 2, 4, 2), color="springgreen"))
# ax.add_collection(mpl.collections.LineCollection(anchor_edges[0, an].numpy(), color="springgreen"))
ax.add_collection(mpl.collections.PatchCollection(verts, color='tomato', alpha=1, zorder=250))
plt.show()

# %%
I, bb, an = e
fig, ax = plt.subplots(figsize=(8, 6))
ax.set(
        ylim=[0, 384],
        xlim=[0, 512],
        xticks=list(range(0, 512,int(np.ceil(512/12)))),
        yticks=list(range(0, 384, int(np.ceil(384/9)))),
        )
lines = []
verts = []
points = []
for i in range(8):
    point = result[I, bb, an, i]
    if point[0] == 0:
        continue
    verts.append(Circle(point, radius=2, color="tomato", zorder=10))
    points.append(point)
for i in range(1, 12, 1):
    line = i * 512/12
    lines.append([(line, 0), (line, 384)])
for i in range(1, 9, 1):
    line = i * 384/9
    lines.append([(0, line), (512, line)])
grid_lines = mpl.collections.LineCollection(lines, colors='black', lw=1, alpha=1, zorder=200)
ax.add_collection(grid_lines)
ax.add_collection(mpl.collections.LineCollection(label_edges[I, bb]))
# ax.add_collection(mpl.collections.LineCollection(anchor_edges[0, an::108].numpy().reshape(num_anchors * 2, 4, 2), color="springgreen"))
ax.add_collection(mpl.collections.LineCollection(anchor_edges[I, an].numpy(), color="springgreen"))
ax.add_collection(mpl.collections.PatchCollection(verts, color='tomato', alpha=1, zorder=250))
ax.add_patch(Polygon(points, color="red", alpha=.3))
plt.show()

# %%
fig, ax = plt.subplots(figsize=(8, 6))
ax.set(
        ylim=[0, 384],
        xlim=[0, 512],
        xticks=list(range(0, 512,int(np.ceil(512/12)))),
        yticks=list(range(0, 384, int(np.ceil(384/9)))),
        )
lines = []
for i in range(1, 12, 1):
    line = i * 512/12
    lines.append([(line, 0), (line, 384)])
for i in range(1, 9, 1):
    line = i * 384/9
    lines.append([(0, line), (512, line)])
grid_lines = mpl.collections.LineCollection(lines, colors='black', lw=1, alpha=1, zorder=200)
ax.add_collection(grid_lines)
for i in range(24):
    ax.add_collection(mpl.collections.LineCollection(step2[0, 0, i]))
for i in range(9):
    ax.add_collection(mpl.collections.LineCollection(anchr_edges[0, i:108:9].numpy().reshape(24, 4, 2), color="springgreen"))
    # ax.add_collection(mpl.collections.LineCollection(anchr_edges[0, i+108:216:9].numpy().reshape(24, 4, 2), color="tomato"))
    # ax.add_collection(mpl.collections.LineCollection(anchr_edges[0, i+216:324:9].numpy().reshape(24, 4, 2), color="orange"))
# plt.savefig("./images/anchor_box_illustration.png")
plt.show()

# %%
fig, axs = plt.subplots(2, 1, figsize=(8, 10))
# axs = np.concatenate([ax1, ax2], axis=-1)
for img, ax in enumerate(axs):
    lines = []
    for i in range(1, 12, 1):
        line = i * 512/12
        lines.append([(line, 0), (line, 384)])
    for i in range(1, 9, 1):
        line = i * 384/9
        lines.append([(0, line), (512, line)])
    grid_lines = mpl.collections.LineCollection(lines, colors='black', lw=1, ls='--', alpha=.4)
    ax.set(
            ylim=[0, 384],
            xlim=[0, 512],
            xticks=list(range(0, 512,int(np.ceil(512/12)))),
            yticks=list(range(0, 384, int(np.ceil(384/9)))),
            )
    ax.axis('off')
    ax.imshow(load_img(images[img], target_size=(384, 512)))
    ax.add_collection(grid_lines)
    for idx, box in enumerate(label_corners[img]):
        bbox, arrow = display_label(np.reshape(labels, (labels.shape[0],) + (12 * 9, labels.shape[-1]))[img, idx, 14:], ax, color=next(color))
        ax.add_patch(bbox)
        ax.add_patch(arrow)
        # ax.add_patch(Polygon(label_corners.reshape(269, 12 * 9, 4, 2)[img, idx], fill=None, edgecolor="tomato", lw=5))
fig.tight_layout()
plt.savefig("./images/bounding_box_examples_2.png")
plt.show()

# %%
fig, [ax1, ax2, ax3, ax4] = plt.subplots(4, 3, figsize=(12, 12))
axs = np.concatenate([ax1, ax2, ax3, ax4], axis=-1)
for img, ax in enumerate(axs):
    lines = []
    for i in range(1, 12, 1):
        line = i * 512/12
        lines.append([(line, 0), (line, 384)])
    for i in range(1, 9, 1):
        line = i * 384/9
        lines.append([(0, line), (512, line)])
    grid_lines = mpl.collections.LineCollection(lines, colors='black', lw=1, ls='--', alpha=.4)
    ax.set(
            ylim=[0, 384],
            xlim=[0, 512],
            xticks=list(range(0, 512,int(np.ceil(512/12)))),
            yticks=list(range(0, 384, int(np.ceil(384/9)))),
            )
    ax.axis('off')
    ax.imshow(load_img(images[img], target_size=(384, 512)))
    ax.add_collection(grid_lines)
    for idx, box in enumerate(label_corners[img]):
        bbox, arrow = display_label(np.reshape(labels, (labels.shape[0],) + (12 * 9, labels.shape[-1]))[img, idx, 14:], ax, color=next(color))
        ax.add_patch(bbox)
        ax.add_patch(arrow)
        # ax.add_patch(Polygon(box, fill=None, edgecolor="tomato", lw=5))
fig.tight_layout()
plt.savefig("./images/bounding_box_examples_16.png")
plt.show()
