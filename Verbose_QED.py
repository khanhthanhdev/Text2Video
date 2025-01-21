self.play(
    LaggedStart(
        Create(e_wave),
        Create(b_wave),
        lag_ratio=0.5,
        run_time=3
    )
)
self.play(
    FadeIn(label_E, shift=RIGHT),
    FadeIn(label_B, shift=RIGHT),
    Create(propagation_arrow),
    FadeIn(prop_label),
    run_time=3
) 