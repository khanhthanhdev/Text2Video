from manim import *

class DotProductScene(Scene):
    def construct(self):
        # Title
        title = Tex("Vector Dot Product", font_size=48)
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))

        # Create axes
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-3, 3, 1],
            x_length=8,
            y_length=6,
            axis_config={"color": BLUE},
        )
        axes_labels = axes.get_axis_labels(x_label="x", y_label="y")
        self.play(Create(axes), Write(axes_labels))
        self.wait(0.5)

        # Create vectors
        vector_a = Vector([3, 2], color=RED)
        vector_b = Vector([1, 3], color=GREEN)
        vector_a_label = MathTex("\\vec{a}", color=RED).next_to(vector_a.get_end(), UP)
        vector_b_label = MathTex("\\vec{b}", color=GREEN).next_to(vector_b.get_end(), RIGHT)

        self.play(GrowArrow(vector_a), Write(vector_a_label))
        self.play(GrowArrow(vector_b), Write(vector_b_label))
        self.wait(1)

        # Projection animation
        projection_line = DashedLine(
            vector_b.get_end(),
            [vector_b.get_end()[0], vector_a.get_end()[1], 0],
            color=YELLOW,
        )
        projection_label = MathTex("\\vec{a} \\cdot \\vec{b} = |\\vec{a}| |\\vec{b}| \\cos(\\theta)").to_edge(UP)

        self.play(Write(projection_label))
        self.wait(0.5)
        self.play(Create(projection_line))
        self.wait(1)

        # Angle between vectors
        angle = Angle(vector_a, vector_b, radius=0.5, color=YELLOW)
        angle_label = MathTex("\\theta").next_to(angle, RIGHT, buff=0.15)

        self.play(Create(angle), Write(angle_label))
        self.wait(1)

        # Dot product calculation
        dot_product = MathTex(
            "\\vec{a} \\cdot \\vec{b} = ",
            "a_x b_x + a_y b_y",
            " = ",
            "3 \\cdot 1 + 2 \\cdot 3",
            " = ",
            "3 + 6",
            " = ",
            "9"
        ).to_edge(DOWN)

        self.play(Write(dot_product[0:2]))
        self.wait(0.5)
        self.play(Transform(dot_product[0:2], dot_product[0:4]))
        self.wait(0.5)
        self.play(Transform(dot_product[0:4], dot_product[0:6]))
        self.wait(0.5)
        self.play(Transform(dot_product[0:6], dot_product))
        self.wait(2)

        # Clean up
        self.play(
            FadeOut(projection_line),
            FadeOut(angle),
            FadeOut(angle_label),
            FadeOut(projection_label),
            FadeOut(dot_product),
        )
        self.wait(0.5)

        # Final visualization
        final_text = Tex("Dot product measures", " how much one vector", " goes in the direction of another")
        final_text[1].set_color(RED)
        final_text[2].set_color(GREEN)
        final_text.to_edge(UP)

        self.play(Write(final_text))
        self.wait(2)
