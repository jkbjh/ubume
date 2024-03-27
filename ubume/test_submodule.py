import sys
import time

print("test_submodule imported")

for i in range(50):
    print("\r importing test_submodule" + "." * i, end="")
    sys.stdout.flush()
    time.sleep(0.1)
print("")
print("submodule imported...")
