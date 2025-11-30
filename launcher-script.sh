echo "Running launcher script..."
echo "Detecting OS system..."

# --------------------------------------------------
# 1. Make sure it's macOS
# --------------------------------------------------
OS_TYPE="$(uname -s)"

if [[ "$OS_TYPE" != "Darwin" ]]; then 
    echo "macOS is not detected. This script only supports macOS."
    exit 1
fi

echo "macOS detected. Continuing with the script..."

# --------------------------------------------------
# 2. Detect architecture (Intel vs Apple Silicon)
# --------------------------------------------------
ARCH=$(uname -m)

echo -n "Detecting CPU architecture... "

# Use 4.53 Release
if [[ "$ARCH" == "arm64" ]]; then
    echo "Apple Silicion dectected." 
    DOCKER_URL="https://desktop.docker.com/mac/main/arm64/211793/Docker.dmg?utm_source=docker&utm_medium=webreferral&utm_campaign=docs-driven-download-mac-arm64"
else
    echo "Intel architecture detected."
    DOCKER_URL="https://desktop.docker.com/mac/main/amd64/211793/Docker.dmg?utm_source=docker&utm_medium=webreferral&utm_campaign=docs-driven-download-mac-amd64"
fi

# --------------------------------------------------
# 3. Download Docker installer
# --------------------------------------------------
echo "Downloading Docker Desktop for macOS..."
echo "Download URL: $DOCKER_URL"
curl -L -o Docker.dmg "$DOCKER_URL"

if [[ $? -ne 0 ]]; then
    echo "Failed to download Docker Desktop. Please check your internet connection and try again."
    exit 1
fi

echo "Download completed."

# --------------------------------------------------
# 4. Open the Docker installer
# --------------------------------------------------
echo ""
echo "Opening Docker installer..."
open Docker.dmg

echo ""
echo "Please complete the Docker installation manually."
echo "If you encounter any issues, please make sure to update your macOS to the latest version and try again."
echo "After installation, ensure Docker Desktop is running."
read -p "Press ENTER once Docker is installed and started..."

# --------------------------------------------------
# 5. Verify Docker installation
# --------------------------------------------------
echo ""
echo "Checking Docker installation..."

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is still not installed. Exiting."
    exit 1
fi

echo "Docker installed: &(docker --version)"