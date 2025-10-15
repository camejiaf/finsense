#!/usr/bin/env python3
"""
FinSense Setup Script
Quick setup for development environment
"""

import os
import sys
import subprocess
import platform


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True,
                                check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    print("🚀 Setting up FinSense Development Environment")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)

    print(
        f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Setup backend
    print("\n📦 Setting up backend...")
    if not os.path.exists("backend"):
        print("❌ Backend directory not found")
        sys.exit(1)

    os.chdir("backend")

    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install Python dependencies")
        sys.exit(1)

    os.chdir("..")

    # Setup frontend
    print("\n📦 Setting up frontend...")
    if not os.path.exists("frontend"):
        print("❌ Frontend directory not found")
        sys.exit(1)

    os.chdir("frontend")

    # Check if Node.js is installed
    try:
        subprocess.run("node --version", shell=True,
                       check=True, capture_output=True)
        print("✅ Node.js detected")
    except subprocess.CalledProcessError:
        print("❌ Node.js not found. Please install Node.js 18+")
        sys.exit(1)

    # Install Node.js dependencies
    if not run_command("npm install", "Installing Node.js dependencies"):
        print("❌ Failed to install Node.js dependencies")
        sys.exit(1)

    os.chdir("..")

    # Create .env file if it doesn't exist
    env_path = "backend/.env"
    if not os.path.exists(env_path):
        print("\n📝 Creating environment file...")
        with open(env_path, "w") as f:
            f.write("# FinSense Environment Configuration\n")
            f.write("ALPHA_VANTAGE_API_KEY=your_api_key_here\n")
            f.write("MIN_REQUEST_INTERVAL=60\n")
        print("✅ Created backend/.env file")
        print("⚠️  Please add your Alpha Vantage API key to backend/.env")

    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Add your Alpha Vantage API key to backend/.env")
    print("2. Run: ./start_dev.bat (Windows) or start_dev.sh (Linux/Mac)")
    print("3. Open http://localhost:3000 in your browser")
    print("\n🔗 Get your free Alpha Vantage API key at: https://www.alphavantage.co/support/#api-key")


if __name__ == "__main__":
    main()
