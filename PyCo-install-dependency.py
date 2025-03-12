import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    dependencies = [
        "pygame",
        "socket"
    ]
    
    print("Checking and installing dependencies...")
    for dependency in dependencies:
        try:
            __import__(dependency)
            print(f"{dependency} is already installed.")
        except ImportError:
            print(f"{dependency} is not installed. Installing...")
            install(dependency)
            print(f"{dependency} has been installed successfully.")
    
    print("All dependencies are installed. You can now run the game.")

if __name__ == "__main__":
    main()
