import sys
try:
    import numpy as np
    print("numpy:", np.__version__)
except Exception as e:
    print("numpy error:", e)

try:
    import scipy
    print("scipy:", scipy.__version__)
except Exception as e:
    print("scipy error:", e)

try:
    import sklearn
    print("sklearn:", sklearn.__version__)
except Exception as e:
    print("sklearn error:", e)
