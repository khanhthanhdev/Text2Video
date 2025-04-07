from manim import *

class DotProductScene(Scene):
    def construct(self):
        # Title
        title = Tex("Vector Dot Product", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # Create axes
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-3, 3, 1],
            x_length=8,
            y_length=6,
            axis_config={"color": BLUE},
        )
        axes.center()
        self.play(Create(axes))
        self.wait(0.5)

        # Create vectors
        vector_a = Vector([3, 2], color=RED)
        vector_a_label = MathTex("\\vec{a}", color=RED).next_to(vector_a.get_end(), RIGHT)
        
        vector_b = Vector([1, -2], color=GREEN)
        vector_b_label = MathTex("\\vec{b}", color=GREEN).next_to(vector_b.get_end(), LEFT)
        
        self.play(GrowArrow(vector_a), Write(vector_a_label))
        self.play(GrowArrow(vector_b), Write(vector_b_label))
        self.wait(1)

        # Show angle between vectors
        angle = Angle(vector_a, vector_b, radius=0.8, color=YELLOW)
        angle_label = MathTex("\\theta").move_to(angle.point_from_proportion(0.5) * 1.2)
        
        self.play(Create(angle), Write(angle_label))
        self.wait(1)

        # Dot product formula
        formula = MathTex(
            "\\vec{a} \\cdot \\vec{b} = |\\vec{a}| |\\vec{b}| \\cos\\theta",
            font_size=36
        )
        formula.to_edge(DOWN)
        
        self.play(Write(formula))
        self.wait(2)

        # Calculate components
        components = MathTex(
            "\\vec{a} \\cdot \\vec{b} = a_x b_x + a_y b_y",
            font_size=36
        )
        components.next_to(formula, UP, buff=0.5)
        
        self.play(Write(components))
        self.wait(2)

        # Numerical calculation
        calculation = MathTex(
            "= (3)(1) + (2)(-2) = 3 - 4 = -1",
            font_size=36
        )
        calculation.next_to(components, DOWN, aligned_edge=LEFT)
        
        self.play(Write(calculation))
        self.wait(3)

        # Fade out
        self.play(*[FadeOut(mob) for mob in self.mobjects])
