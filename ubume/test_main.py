import time
import test_submodule

print("test_main imported")
print(f"__name__ is set to {__name__}")

def main(args):
    print("calling main()")
    pass

if __name__ == "__main__":
    print("__main__ called")
    main([])
