import os, sys
sys.path.insert(0, r'M:\Geo Studio\GeoStudio')
from app.core.processing.algorithm_registry import AlgorithmRegistry

algos = AlgorithmRegistry.get_all_algorithms()
print(f"Total algorithms in registry: {len(algos)}")
by_dtype = {}
for a in algos:
    by_dtype.setdefault(a.dialog_type, []).append(a.algo_id)

for dt, ids in sorted(by_dtype.items()):
    print(f"[{dt}] ({len(ids)} algos): {', '.join(ids[:5])}{' ...' if len(ids)>5 else ''}")
