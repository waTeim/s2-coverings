from src.lib.geo.constrained_s2_region_converer import ConstrainedS2RegionCoverer

def test_init():
    max = 10
    min = 9
    converter = ConstrainedS2RegionCoverer(min, max)
    assert int(converter.max_level()) == max
    assert int(converter.min_level()) == min
