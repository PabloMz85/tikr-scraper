#!/usr/bin/env bash
set -e

echo "==============================="
echo "🚀 Installing Google Chrome + matching ChromeDriver (Headless Ready)"
echo "==============================="

# --- Update system ---
sudo apt update -y
sudo apt install -y wget unzip gnupg2 apt-transport-https curl jq lsb-release

# --- Detect package suffix for 64-bit time_t transition (Ubuntu 24.04+) ---
PKG_SUFFIX=""
if apt-cache search libcups2t64 | grep -q libcups2t64; then
  PKG_SUFFIX="t64"
  echo "Detected Ubuntu 24.04 or newer — using *t64* packages."
else
  echo "Detected Ubuntu 22.04 or older — using standard package names."
fi

# --- Install Chrome dependencies ---
sudo apt install -y \
  "libasound2${PKG_SUFFIX}" \
  "libatk-bridge2.0-0${PKG_SUFFIX}" \
  "libatk1.0-0${PKG_SUFFIX}" \
  "libcups2${PKG_SUFFIX}" \
  "libdrm2" \
  "libgbm1" \
  "libgtk-3-0${PKG_SUFFIX}" \
  "libnspr4" \
  "libnss3" \
  "libxcomposite1" \
  "libxdamage1" \
  "libxfixes3" \
  "libxkbcommon0" \
  "libxrandr2" \
  xdg-utils \
  fonts-liberation

# --- Install Google Chrome (stable) ---
if ! command -v google-chrome >/dev/null 2>&1; then
  echo "📦 Installing Google Chrome..."
  wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  sudo apt install -y ./google-chrome-stable_current_amd64.deb
  rm -f google-chrome-stable_current_amd64.deb
else
  echo "✅ Google Chrome already installed."
fi

# --- Verify Chrome installation ---
if ! command -v google-chrome >/dev/null 2>&1; then
  echo "❌ Chrome installation failed."
  exit 1
fi

CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
CHROME_MAJOR=$(echo "$CHROME_VERSION" | cut -d '.' -f 1)
echo "✅ Installed Google Chrome version: $CHROME_VERSION (major: $CHROME_MAJOR)"

# --- Fetch matching ChromeDriver using CfT API ---
echo "🌐 Fetching ChromeDriver for Chrome $CHROME_VERSION..."
CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json | \
  jq -r --arg ver "$CHROME_MAJOR" '
    .versions[]
    | select(.version | startswith($ver))
    | .downloads.chromedriver[]
    | select(.platform == "linux64")
    | .url' | head -n 1)

if [ -z "$CHROMEDRIVER_URL" ]; then
  echo "⚠️  Could not find an exact ChromeDriver match. Using latest stable version..."
  CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json | \
    jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform == "linux64") | .url')
fi

echo "📦 Downloading from: $CHROMEDRIVER_URL"
wget -q "$CHROMEDRIVER_URL" -O chromedriver.zip
unzip -o chromedriver.zip >/dev/null
sudo mv -f chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver.zip chromedriver-linux64/

# --- Verify both ---
echo
echo "🧩 Chrome version:"
google-chrome --version
echo "🧩 ChromeDriver version:"
chromedriver --version
echo
echo "✅ Chrome + ChromeDriver successfully installed and synchronized!"
echo "Ready for headless Selenium 🚀"