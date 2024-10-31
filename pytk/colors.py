import numpy as np

# colors_hex = [
#     'e6194B',
#     '3cb44b',
#     '4363d8',
#     'ffe119',
# ]

colors_hex = ['fb8072', '80b1d3', 'b3de69', 'fdb462', '8dd3c7', 'ffffb3', 'bebada', 'fccde5', 'd9d9d9']
colors_hex[1] = 'ff0000'

colors_rgb = np.array([list(int(h[i:i+2], 16) for i in (0, 2, 4)) for h in colors_hex])


colors_rgba = np.concatenate([colors_rgb, 255 * np.ones(colors_rgb.shape[0])[:, None]], axis=1)
colors_rgba = np.concatenate([np.zeros(4)[None, :], colors_rgba], axis=0)

color_map = np.repeat(colors_rgba[None, :, :], 10, axis=0).reshape(-1, 4)
color_map = np.repeat(color_map[None, :, :], 10, axis=0).reshape(-1, 4).astype(np.uint8)