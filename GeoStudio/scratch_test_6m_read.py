import time, laspy, numpy as np

path = r'C:\Users\pc\Downloads\M-34-38-C-d-2-3-2.laz'
t0 = time.perf_counter()
with laspy.open(path) as fh:
    total = fh.header.point_count
    # max_points = 6,000,000
    step = max(1, total // 6000000)
    las = fh.read()
    x = np.array(las.x[::step], dtype=np.float32)
    y = np.array(las.y[::step], dtype=np.float32)
    z = np.array(las.z[::step], dtype=np.float32)
    r = np.array(las.red[::step])
    g = np.array(las.green[::step])
    b = np.array(las.blue[::step])

read_time = time.perf_counter() - t0
print(f"Read {len(x):,} points in {read_time:.2f}s")
print(f"Points sampled: {len(x):,} out of {total:,} ({len(x)/total*100:.1f}%)")
