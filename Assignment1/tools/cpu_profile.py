# tools/cpu_profile.py
import cProfile
import pstats
from src.geo_matcher import find_closest_location

def workload():
    target = (42.3601, -71.0589)
    candidates = [(42.0 + i * 1e-4, -71.0 - i * 1e-4) for i in range(20000)]
    return find_closest_location(target, candidates)

def main():
    profiler = cProfile.Profile()
    profiler.enable()

    _ = workload()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumulative")
    stats.print_stats(20)   # print 20 most time cost 

if __name__ == "__main__":
    main()
