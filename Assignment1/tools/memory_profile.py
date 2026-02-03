# tools/memory_profile.py
import tracemalloc
from src.geo_matcher import find_closest_location

def main():
    # 构造一些“候选点”，模拟大输入
    target = (42.3601, -71.0589)
    candidates = [(42.0 + i * 1e-4, -71.0 - i * 1e-4) for i in range(20000)]

    tracemalloc.start()

    # 运行你要分析的函数
    _ = find_closest_location(target, candidates)

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    print("Top 10 memory allocations:")
    for stat in top_stats[:10]:
        print(stat)

if __name__ == "__main__":
    main()
