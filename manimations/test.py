from manim import *

class Screen(Scene):
    def construct(self):
        # Step 1: Define the function and interval
        func = lambda x: x**2
        interval = [0, 3]
        
        # Create axes
        axes = Axes(
            x_range=[0, 3.5, 0.5],
            y_range=[0, 10, 2],
            axis_config={"color": BLUE},
            tips=False,
        )
        axes_labels = axes.get_axis_labels(x_label="x", y_label="f(x)")
        
        # Plot the function
        graph = axes.plot(func, color=YELLOW)
        graph_label = axes.get_graph_label(graph, label="f(x) = x^2", x_val=2.5, direction=UP)
        
        # Step 2: Introduce the concept of area under the curve
        area = axes.get_area(graph, x_range=interval, color=[BLUE_D, GREEN])
        area_label = Text("Area under the curve", font_size=24).next_to(area, UP)
        
        # Step 3: Visualize summation of infinitesimally small quantities
        riemann_rectangles = axes.get_riemann_rectangles(
            graph, x_range=interval, dx=0.5, input_sample_type="left", color=[BLUE_D, GREEN], fill_opacity=0.5
        )
        riemann_label = Text("Summation of small rectangles", font_size=24).next_to(riemann_rectangles, DOWN)
        
        # Animate the introduction of the axes, graph, and area
        self.play(Create(axes), Write(axes_labels))
        self.play(Create(graph), Write(graph_label))
        self.wait(1)
        self.play(FadeIn(area), Write(area_label))
        self.wait(2)
        
        # Transform the area into Riemann rectangles
        self.play(Transform(area, riemann_rectangles), Write(riemann_label))
        self.wait(2)
        
        # Step 4: Gradually reduce the width of the rectangles to show infinitesimally small quantities
        for dx in [0.25, 0.1, 0.05]:
            new_riemann_rectangles = axes.get_riemann_rectangles(
                graph, x_range=interval, dx=dx, input_sample_type="left", color=[BLUE_D, GREEN], fill_opacity=0.5
            )
            self.play(Transform(riemann_rectangles, new_riemann_rectangles))
            self.wait(1)
        
        # Final explanation
        integral_label = MathTex(r"\int_{0}^{3} x^2 \, dx").scale(1.5).to_edge(UP)
        self.play(Write(integral_label))
        self.wait(3)