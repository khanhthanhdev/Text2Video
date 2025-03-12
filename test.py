%%manim -qm Screen

from manim import *
class GiaiThichTichPhan(Scene):
def construct(self):
# Thiết lập trục tọa độ
plane = NumberPlane(
x_range=[-1, 10, 1],
y_range=[-1, 10, 1],
axis_config={"color": BLUE}
 )
self.play(Create(plane))
# Định nghĩa hàm số
def ham_so(x):
return 0.1  (x - 5) * 2 + 2
# Vẽ đường cong
graph = plane.plot(ham_so, color=WHITE)
self.play(Create(graph))
# Vẽ các hình chữ nhật dưới đường cong (tổng Riemann)
x_min = 1
x_max = 9
dx = 0.5
rectangles = plane.get_riemann_rectangles(
graph,
x_range=[x_min, x_max],
dx=dx,
stroke_width=0.1,
stroke_color=WHITE,
fill_opacity=0.5,
fill_color=YELLOW,
 )
self.play(Create(rectangles))
# Thêm tiêu đề
tieu_de = Text("Giải thích khái niệm tích phân", font_size=24, color=WHITE).to_edge(UP)
self.play(Write(tieu_de))
self.wait(2)
