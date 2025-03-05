from s2geometry import S2RegionCoverer


class ConstrainedS2RegionCoverer(S2RegionCoverer):
    """
    An S2RegionCoverer, commonly used throughout the cli
    """

    def __init__(self, min_level, max_level):
        super().__init__()
        self.set_max_level(max_level)
        self.set_min_level(min_level)
