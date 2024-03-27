import time
import test_submodule

print("test_main.py: test_main imported")
print(f"test_main.py: __name__ is set to {__name__}")

def main(args):
    print("test_main.py: calling main()")
    pass

if __name__ == "__main__":
    print("test_main.py: __main__ called !!!!!!!!!!!!!!!!")
    main([])
