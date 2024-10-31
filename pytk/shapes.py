import vedo

class Box(vedo.Assembly):

    def __init__(self, paint_size, spacing, lw, c):

        self.paint_size = paint_size
        self.spacing = spacing.copy()
        
        box_size = self.paint_size * self.spacing
        len_x, len_y, len_z = box_size
        
        sx, sy, sz = -len_x / 2, -len_y / 2, -len_z / 2
        ex, ey, ez = sx + len_x, sy + len_y, sz + len_z

        line1 = vedo.Line([sx, sy, sz], [ex, sy, sz], lw=lw, c=c)
        line2 = vedo.Line([ex, sy, sz], [ex, ey, sz], lw=lw, c=c)
        line3 = vedo.Line([ex, ey, sz], [sx, ey, sz], lw=lw, c=c)
        line4 = vedo.Line([sx, ey, sz], [sx, sy, sz], lw=lw, c=c)
        line5 = vedo.Line([sx, sy, ez], [ex, sy, ez], lw=lw, c=c)
        line6 = vedo.Line([ex, sy, ez], [ex, ey, ez], lw=lw, c=c)
        line7 = vedo.Line([ex, ey, ez], [sx, ey, ez], lw=lw, c=c)
        line8 = vedo.Line([sx, ey, ez], [sx, sy, ez], lw=lw, c=c)
        line9 = vedo.Line([sx, sy, ez], [sx, sy, sz], lw=lw, c=c)
        line10 = vedo.Line([ex, sy, ez], [ex, sy, sz], lw=lw, c=c)
        line11 = vedo.Line([ex, ey, ez], [ex, ey, sz], lw=lw, c=c)
        line12 = vedo.Line([sx, ey, ez], [sx, ey, sz], lw=lw, c=c)
        
        self.lines = [line1, line2, line3, line4, line5, line6, line7, line8, line9, line10, line11, line12]

        super().__init__(*self.lines)
    
    def color(self, rgb):
        for line in self.lines:
            line.c(rgb)

class CrossCursor(vedo.Assembly):

    def __init__(self, size, lw, c):
        
        len_x, len_y, len_z = size, size, size

        p1 = [-len_x / 2, 0, 0]
        p2 = [len_x / 2, 0, 0]
        p3 = [0, -len_y / 2, 0]
        p4 = [0, len_y / 2, 0]
        p5 = [0, 0, -len_z / 2]
        p6 = [0, 0, len_z / 2]
        
        line1 = vedo.Line(p1, p2, lw=lw, c=c)
        line2 = vedo.Line(p3, p4, lw=lw, c=c)
        line3 = vedo.Line(p5, p6, lw=lw, c=c)

        self.lines = [line1, line2, line3]

        super().__init__(*self.lines)
    
    def color(self, rgb):
        for line in self.lines:
            line.c(rgb)