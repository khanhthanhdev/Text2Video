from manim import *

class DotProductAnimation(Scene):
    def construct(self):
        # Title
        title = Tex("Vector Dot Product", font_size=48)
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))

        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            axis_config={"color": BLUE},
        )
        self.play(Create(axes))
        self.wait(0.5)

        # Create vectors
        vec_a = Vector([2, 1], color=RED)
        vec_b = Vector([1, 2], color=GREEN)
        
        vec_a_label = MathTex("\\vec{a}", color=RED).next_to(vec_a.get_end(), UP)
        vec_b_label = MathTex("\\vec{b}", color=GREEN).next_to(vec_b.get_end(), RIGHT)
        
        self.play(GrowArrow(vec_a), Write(vec_a_label))
        self.play(GrowArrow(vec_b), Write(vec_b_label))
        self.wait(1)

        # Show projection
        dot_product = MathTex("\\vec{a} \\cdot \\vec{b} = |\\vec{a}| |\\vec{b}| \\cos(\\theta)")
        dot_product.to_edge(UP)
        self.play(Write(dot_product))
        self.wait(1)

        # Angle between vectors
        angle = Angle(vec_a, vec_b, radius=0.5, other_angle=False)
        angle_label = MathTex("\\theta").next_to(angle, RIGHT, buff=0.15)
        self.play(Create(angle), Write(angle_label))
        self.wait(1)

        # Calculate dot product
        calculation = MathTex(
            "\\vec{a} \\cdot \\vec{b} = (2)(1) + (1)(2) = 4",
            font_size=36
        )
        calculation.next_to(dot_product, DOWN)
        self.play(Write(calculation))
        self.wait(2)

        # Clean up
        self.play(
            FadeOut(angle),
            FadeOut(angle_label),
            FadeOut(calculation),
            FadeOut(dot_product),
        )
        self.wait(0.5)

        # Geometric interpretation
        projection_line = DashedLine(
            vec_b.get_end(),
            [vec_b.get_end()[0], vec_a.get_end()[1], 0],
            color=YELLOW
        )
        projection_label = MathTex(
            "|\\vec{a}| \\cos(\\theta)",
            color=YELLOW
        ).next_to(projection_line, LEFT)

        self.play(
            Create(projection_line),
            Write(projection_label
        ))
        self.wait(1)

        final_interpretation = MathTex(
            "\\vec{a} \\cdot \\vec{b} = |\\vec{b}| \\times (\\text{Projection of } \\vec{a} \\text{ on } \\vec{b})",
            font_size=36
        ).to_edge(DOWN)
        
        self.play(Write(final_interpretation))
        self.wait(2)

        # Fade out everything
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(1)  # Add a final wait to ensure the video doesn't cut off abruptly
