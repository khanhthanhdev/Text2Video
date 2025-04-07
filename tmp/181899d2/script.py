from manim import *

class VectorDotProduct(Scene):
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
        axes_labels = axes.get_axis_labels(x_label="x", y_label="y")

        # Create vectors
        vector_a = Vector([2, 1], color=RED)
        vector_b = Vector([1, 2], color=GREEN)
        vector_a_label = MathTex("\\vec{a}").next_to(vector_a, RIGHT, buff=0.1)
        vector_b_label = MathTex("\\vec{b}").next_to(vector_b, UP, buff=0.1)

        # Dot product formula
        formula = MathTex("\\vec{a} \\cdot \\vec{b} = ", "a_x b_x + a_y b_y").to_edge(UP)
        formula_part1 = formula[0]
        formula_part2 = formula[1]

        # Projection lines
        projection_a = DashedLine(
            start=vector_a.get_end(),
            end=[vector_a.get_end()[0], 0],
            color=RED,
            stroke_width=2,
        )
        projection_b = DashedLine(
            start=vector_b.get_end(),
            end=[0, vector_b.get_end()[1]],
            color=GREEN,
            stroke_width=2,
        )

        # Components
        a_x = Line([0, 0, 0], [vector_a.get_end()[0], 0, 0], color=RED)
        a_y = Line([vector_a.get_end()[0], 0, 0], vector_a.get_end(), color=RED)
        b_x = Line([0, 0, 0], [0, vector_b.get_end()[1], 0], color=GREEN)
        b_y = Line([0, vector_b.get_end()[1], 0], vector_b.get_end(), color=GREEN)

        # Component labels
        a_x_label = MathTex("a_x").next_to(a_x, DOWN, buff=0.1)
        a_y_label = MathTex("a_y").next_to(a_y, RIGHT, buff=0.1)
        b_x_label = MathTex("b_x").next_to(b_x, LEFT, buff=0.1)
        b_y_label = MathTex("b_y").next_to(b_y, UP, buff=0.1)

        # Animation sequence
        self.play(Create(axes), Write(axes_labels))
        self.wait(0.5)
        self.play(GrowArrow(vector_a), Write(vector_a_label))
        self.play(GrowArrow(vector_b), Write(vector_b_label))
        self.wait(0.5)
        self.play(Write(formula_part1))
        self.wait(0.5)

        # Show projections and components
        self.play(Create(projection_a), Create(projection_b))
        self.wait(0.5)
        self.play(Create(a_x), Create(a_y), Write(a_x_label), Write(a_y_label))
        self.play(Create(b_x), Create(b_y), Write(b_x_label), Write(b_y_label))
        self.wait(0.5)

        # Show dot product calculation
        self.play(Write(formula_part2))
        self.wait(1)

        # Final calculation
        final_calc = MathTex("\\vec{a} \\cdot \\vec{b} = ", "(2)(1) + (1)(2) = 4").to_edge(UP)
        self.play(Transform(formula, final_calc))
        self.wait(2)

        # Clean up
        self.play(*[FadeOut(mob) for mob in self.mobjects])
