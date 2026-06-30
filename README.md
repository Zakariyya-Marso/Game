# Python Life Simulator

Welcome to Python Life Simulator, an immersive 3D indie game built using the Python programming language and the Ursina Engine (powered by Panda3D). Explore a sandbox world featuring interactive 3D assets, custom mechanics, and full cross-platform compatibility!

---

## How to Download & Play

Every time updates are pushed to this repository, GitHub Actions automatically compiles fresh standalone packages for Windows, macOS, and Linux. You don't even need Python installed on your computer to play!

1. Go to the Actions tab at the top of this GitHub repository.
2. Click on the latest green automated build run.
3. Scroll down to the Artifacts section at the bottom of the page.
4. Download the ZIP package built for your operating system.

---

## Installation Guides per Platform

### Windows (.exe)
1. Download and extract the game-distribution-windows-latest ZIP file.
2. Open the extracted folder, look for main.exe, and double-click to launch.
3. Note: Since this is an independent indie build, Microsoft SmartScreen might show a blue pop-up stating "Windows protected your PC". Simply click "More Info" and then select "Run Anyway".

### macOS (.dmg)
1. Download the game-distribution-macos-latest ZIP file and open the .dmg installer.
2. Drag the game app bundle into your Applications folder.
3. Note: On modern macOS versions, Gatekeeper might block unverified developers. To play, go to your Mac's System Settings -> Privacy & Security, scroll down to the security section, and click "Open Anyway".

### Linux Mint / Ubuntu (Binary)
1. Download and extract the game-distribution-ubuntu-latest ZIP file.
2. Open a terminal window inside the extracted directory where the file named main is located.
3. Mark the binary file as executable by running this command:
   chmod +x main
4. Launch the game from your terminal by running this command:
   ./main
   
(Optional: You can right-click your Linux Desktop to "Create a new launcher here" and link it to the executable path for a double-click shortcut icon!)

---

## Built With
* Python 3.10 - Core logic and system interactions.
* Ursina Engine - 3D rendering, entity management, and coordinate mapping.
* Panda3D - Underlying game engine frameworks.
* PyInstaller & GitHub Actions - Cloud automation for multi-platform distribution.
