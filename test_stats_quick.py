
import sys
sys.path.insert(0, ".")
import inspect
from src.stats.trend_engine import analyze
sig = inspect.signature(analyze)
print("analyze signature:", sig)
