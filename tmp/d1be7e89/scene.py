from manim import *

class VectorDotProduct(Scene):
    def construct(self):
        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            axis_config={"color": BLUE},
        )
        
        # Create vectors
        vector_a = Vector([2, 1, 0], color=RED)
        vector_b = Vector([1, 2, 0], color=GREEN)
        
        # Label vectors
        label_a = MathTex("\\vec{a}", color=RED).next_to(vector_a.get_end(), RIGHT)
        label_b = MathTex("\\vec{b}", color=GREEN).next_to(vector_b.get_end(), UP)
        
        # Dot product formula
        dot_product_formula = MathTex("\\vec{a} \\cdot \\vec{b} = |\\vec{a}| |\\vec{b}| \\cos(\\theta)")
        dot_product_formula.to_edge(UP)
        
        # Projection animation
        projection_line = DashedLine(
            vector_b.get_end(),
            [vector_b.get_end()[0], vector_a.get_end()[1], 0],
            color=YELLOW
        )
        
        # Angle between vectors
        angle = Angle(vector_a, vector_b, radius=0.5, color=YELLOW)
        angle_label = MathTex("\\theta").next_to(angle, RIGHT, buff=0.15)
        
        # Calculation steps
        calculation = VGroup(
            MathTex("\\vec{a} \\cdot \\vec{b} = (2)(1) + (1)(2) = 4"),
            MathTex("|\\vec{a}| = \\sqrt{2^2 + 1^2} = \\sqrt{5}"),
            MathTex("|\\vec{b}| = \\sqrt{1^2 + 2^2} = \\sqrt{5}"),
            MathTex("\\cos(\\theta) = \\frac{4}{\\sqrt{5} \\cdot \\sqrt{5}} = \\frac{4}{5}")
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(DOWN)
        
        # Animation sequence
        self.play(Create(axes))
        self.wait(0.5)
        self.play(GrowArrow(vector_a), GrowArrow(vector_b))
        self.play(Write(label_a), Write(label_b))
        self.wait(0.5)
        self.play(Write(dot_product_formula))
        self.wait(1)
        self.play(Create(projection_line))
        self.wait(0.5)
        self.play(Create(angle), Write(angle_label))
        self.wait(1)
        
        for step in calculation:
            self.play(Write(step))
            self.wait(0.5)
        
        self.wait(2)
