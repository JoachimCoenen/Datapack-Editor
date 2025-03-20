
# Build instruction for Linux (and maybe macOS, not tested yet)

## Prerequisites
- A Unix like terminal (e.g. bash)
- Python 3.12 installed and available as `python3`

## Checkout and initial setup
1. Clone the git repository using and enter the new project directory
3. Initialize all submodules
4. Create a virtual environment
```bash
git clone https://github.com/JoachimCoenen/Datapack-Editor.git && cd Datapack-Editor
./housekeeping/initialize_submodules.sh
./housekeeping/create_virtual_env.sh
``` 

## Building the App
1. Update all submodules (optional)
2. Update the virtual environment (optional)
3. run the build script
```bash
./housekeeping/update_submodules.sh
./housekeeping/update_virtual_env.sh
./housekeeping/build_app.sh
```
The app will be in `./build/dist/` called `DatapackEditor`.