import re
import numpy as np
from manim import *

class MLAnimationGenerator:
    def __init__(self):
        self.templates = {
            'particle_system': self._create_particle_system_template,
            'vector_field': self._create_vector_field_template,
            'optimal_transport': self._create_optimal_transport_template,
            'diffusion': self._create_diffusion_template,
            'wass_distance': self._create_wasserstein_distance_template,
        }

    def _create_particle_system_template(self, params):
        """Creates a particle system visualization with interpolation"""
        class ParticleScene(Scene):
            def construct(self):
                # Create initial and final distributions
                alpha_0 = VGroup(*[Dot(radius=0.05, color=BLUE) for _ in range(50)])
                alpha_0.arrange_in_grid(rows=5, cols=10, buff=0.2)
                alpha_0.shift(LEFT * 3)

                alpha_1 = VGroup(*[Dot(radius=0.05, color=GOLD) for _ in range(50)])
                alpha_1.arrange_in_grid(rows=5, cols=10, buff=0.2)
                alpha_1.shift(RIGHT * 3)

                # Create interpolation path
                def get_alpha_t(t):
                    return VGroup(*[
                        Dot(
                            radius=0.05,
                            color=interpolate_color(BLUE, GOLD, t),
                            point=interpolate(
                                alpha_0[i].get_center(),
                                alpha_1[i].get_center(),
                                t
                            )
                        )
                        for i in range(len(alpha_0))
                    ])

                # Animations
                self.play(Create(alpha_0), Create(alpha_1))
                self.play(
                    UpdateFromAlphaFunc(
                        alpha_0,
                        lambda m, t: m.become(get_alpha_t(t))
                    ),
                    run_time=3
                )
                self.wait()

        return ParticleScene

    def _create_vector_field_template(self, params):
        """Creates a vector field visualization for transport"""
        class VectorFieldScene(Scene):
            def construct(self):
                # Create vector field
                vector_field = VectorField(
                    lambda p: np.array([p[0], p[1], 0]),
                    x_range=[-4, 4, 0.5],
                    y_range=[-3, 3, 0.5],
                    color=LIGHT_GREY
                )

                # Create streamlines
                stream_lines = StreamLines(
                    lambda p: np.array([p[0], p[1], 0]),
                    stroke_width=2,
                    color=SILVER
                )

                # Animations
                self.play(Create(vector_field))
                self.play(stream_lines.create())
                self.wait()

        return VectorFieldScene

    def _create_optimal_transport_template(self, params):
        """Creates visualization for optimal transport map"""
        class OptimalTransportScene(Scene):
            def construct(self):
                # Create grid for transformation visualization
                grid = NumberPlane(
                    x_range=[-4, 4],
                    y_range=[-3, 3],
                    background_line_style={
                        "stroke_color": BLUE_E,
                        "stroke_width": 1,
                        "stroke_opacity": 0.3
                    }
                )

                # Create transformation
                def transport_function(point):
                    x, y, z = point
                    return np.array([
                        x * np.cos(y),
                        y * np.sin(x),
                        0
                    ])

                # Animate grid transformation
                self.play(Create(grid))
                self.play(
                    grid.animate.apply_function(transport_function),
                    run_time=3
                )
                self.wait()

        return OptimalTransportScene

    def _create_diffusion_template(self, params):
        """Creates a diffusion visualization with interpolating measures"""
        class DiffusionScene(Scene):
            def construct(self):
                # Create initial and final distributions
                alpha_0 = VGroup(*[Dot(radius=0.05, color=BLUE) for _ in range(50)])
                alpha_0.arrange_in_grid(rows=5, cols=10, buff=0.2)
                alpha_0.shift(LEFT * 3)

                alpha_1 = VGroup(*[Dot(radius=0.05, color=GOLD) for _ in range(50)])
                alpha_1.arrange_in_grid(rows=5, cols=10, buff=0.2)
                alpha_1.shift(RIGHT * 3)

                # Create interpolation path
                def get_alpha_t(t):
                    return VGroup(*[
                        Dot(
                            radius=0.05,
                            color=interpolate_color(BLUE, GOLD, t),
                            point=interpolate(
                                alpha_0[i].get_center(),
                                alpha_1[i].get_center(),
                                t
                            )
                        )
                        for i in range(len(alpha_0))
                    ])

                # Animations
                self.play(Create(alpha_0), Create(alpha_1))
                self.play(
                    UpdateFromAlphaFunc(
                        alpha_0,
                        lambda m, t: m.become(get_alpha_t(t))
                    ),
                    run_time=3
                )
                self.wait()

        return DiffusionScene

    def _create_wasserstein_distance_template(self, params):
        """Creates a visualization for Wasserstein distance"""
        class WassersteinDistanceScene(Scene):
            def construct(self):
                # Create initial and final distributions
                alpha_0 = VGroup(*[Dot(radius=0.05, color=BLUE) for _ in range(50)])
                alpha_0.arrange_in_grid(rows=5, cols=10, buff=0.2)
                alpha_0.shift(LEFT * 3)

                alpha_1 = VGroup(*[Dot(radius=0.05, color=GOLD) for _ in range(50)])
                alpha_1.arrange_in_grid(rows=5, cols=10, buff=0.2)
                alpha_1.shift(RIGHT * 3)

                # Create optimal transport map
                def transport_function(point):
                    x, y, z = point
                    return np.array([
                        x + 6,  # Move particles to the right
                        y,
                        0
                    ])

                # Animate transport
                self.play(Create(alpha_0), Create(alpha_1))
                self.play(
                    alpha_0.animate.apply_function(transport_function),
                    run_time=3
                )
                self.wait()

        return WassersteinDistanceScene

    def parse_description(self, text):
        """Parse natural language description into scene parameters"""
        params = {}

        # Detect mathematical content
        if any(term in text.lower() for term in ['α', 'ν', 'diffusion', 'wasserstein', 'optimal transport']):
            if 'diffusion' in text.lower():
                params['template'] = 'diffusion'
            elif 'wasserstein' in text.lower():
                params['template'] = 'wass_distance'
            elif 'optimal transport' in text.lower():
                params['template'] = 'optimal_transport'
            elif 'vector field' in text.lower():
                params['template'] = 'vector_field'

        return params

    def generate_scene(self, description):
        """Generate a manim scene based on the description"""
        params = self.parse_description(description)
        template_name = params.pop('template', 'particle_system')  # Default to particle system

        if template_name in self.templates:
            return self.templates[template_name](params)
        else:
            # Fallback to particle system if no specific template matches
            return self.templates['particle_system'](params)

# Example usage:
if __name__ == "__main__":
    # Example description:
    description = """
    **Explanatory Document: Diffusion Models and Optimal Transport**  
    *(Benamou-Brenier Theorem and Wasserstein Distance)*  

    ---

    ### **Key Concepts and Formulas**  
    1. **Dynamic Formulation of Diffusion:**  
       The time-dependent measure \( \alpha_t \) interpolates between \( \alpha_0 \) and \( \alpha_1 \), governed by:  
       \[
       \alpha_t = \left( (1 - t)P_0 + tP_1 \right)_\# (\alpha_0 \otimes \alpha_1)
       \]  
       Here, \( P_0 \) and \( P_1 \) are projection maps, and \( \# \) denotes the pushforward of measures. This describes a probabilistic "flow" blending two distributions over time.  

    2. **Optimal Transport as Energy Minimization:**  
       The velocity field \( \nu_t \) is optimized to transport mass with minimal kinetic energy:  
       \[
       \min_{\nu_t} \left\{ \int \|\nu_t\|_{L^2(\alpha_t)}^2 \, dt \ : \ \text{div}(\alpha_t \nu_t) + \partial_t \alpha_t = 0 \right\}
       \]  
       The continuity equation \( \text{div}(\alpha_t \nu_t) + \partial_t \alpha_t = 0 \) ensures mass conservation.  

    3. **Wasserstein Distance via Benamou-Brenier:**  
       The squared Wasserstein distance \( W_2^2(\alpha_0, \alpha_1) \) quantifies the minimal effort to morph \( \alpha_0 \) into \( \alpha_1 \):  
       \[
       W_2^2(\alpha_0, \alpha_1) = \inf_{T_1} \left\{ \int \|x - T_1(x)\|^2 \, d\alpha_0(x) \ : \ (T_1)_\# \alpha_0 = \alpha_1 \right\}
       \]  
       The optimal map \( T_1 \) aligns with the geodesic path:  
       \[
       \alpha_t = \left( (1 - t)\text{Id} + tT_1 \right)_\# \alpha_0
       \]  
    """

    # Generate scene for the description
    generator = MLAnimationGenerator()
    Scene = generator.generate_scene(description)

    # Render the scene
    scene_instance = Scene()
    scene_instance.render()