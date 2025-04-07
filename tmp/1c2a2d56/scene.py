from manim import *

class DotProductScene(Scene):
    def construct(self):
        # Title
        title = Tex("Vector Dot Product", font_size=48)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        self.wait(0.5)

        # Create axes
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-3, 3, 1],
            axis_config={"color": BLUE},
        )
        self.play(Create(axes))
        self.wait(0.5)

        # Create vectors
        vector_a = Vector([3, 2], color=RED)
        vector_b = Vector([1, 3], color=GREEN)
        vector_a_label = MathTex("\\vec{a}", color=RED).next_to(vector_a.get_end(), RIGHT)
        vector_b_label = MathTex("\\vec{b}", color=GREEN).next_to(vector_b.get_end(), UP)

        self.play(GrowArrow(vector_a), Write(vector_a_label))
        self.wait(0.5)
        self.play(GrowArrow(vector_b), Write(vector_b_label))
        self.wait(1)

        # Projection animation
        projection_line = DashedLine(
            vector_b.get_end(),
            [vector_b.get_end()[0], vector_a.get_end()[1], 0],
            color=YELLOW,
        )
        projection_label = MathTex(
            "\\vec{a} \\cdot \\vec{b} = |\\vec{a}| |\\vec{b}| \\cos(\\theta)",
            font_size=36
        ).next_to(projection_line, DOWN * 2)

        self.play(Create(projection_line), Write(projection_label))
        self.wait(2)

        # Angle between vectors
        angle = Angle(vector_a, vector_b, radius=0.5, color=YELLOW)
        angle_label = MathTex("\\theta", color=YELLOW).next_to(angle, RIGHT, buff=0.1)

        self.play(Create(angle), Write(angle_label))
        self.wait(2)

        # Calculation
        calculation = MathTex(
            "\\vec{a} \\cdot \\vec{b} = (3)(1) + (2)(3) = 9",
            font_size=36
        ).next_to(projection_label, DOWN, buff=0.5)

        self.play(Write(calculation))
        self.wait(3)

        # Fade out
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait()
