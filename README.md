# bmubin - blender mubin tools
Python scripts to facilitate importing a .smubin file into blender

mubin - map unit binary file
## Core functionality
- Asset Library - batch parse colladae assets for use in blender (multithreaded)
- Mubin Import - parse mubin file(s) and build a scene with linked assets from an asset library

Note: 'asset library' in this case just means a folder full of single-asset blend files, 'asset library' as a feature in blender isn't currently mature enough for this use case


## Before Running

### Prerequisites
Blender 
- Version 3.2.1
  - may work with other versions

Python
- Version 3.10.5
    - will probably work with other python 3 versions
    - will definitely not work with python 2

### Set up importables (collada, textures)
- Colladas and textures go in the /collada and /textures folder respectively
  - If you don't have collada files or textures you can batch export them from bfres using Switch Toolbox: https://github.com/KillzXGaming/Switch-Toolbox
    - TBD whether I include a bfres extractor in this repo, likely better served by Switch Toolbox for continued maintenance and updates
  - collada example: mubin_to_blender\collada\TwnObj_Village_Hateno_A-51\TwnObj_Village_HatenoHouse_A_L_02.dae

### Starting Scene
If you want to use a blend file as the base for making an asset or importing a mubin, rename it to starting_scene.blend and put it in the starting_scene folder!

This is also a good way of importing a mubin to an existing blend file. You can also append the root collection from the generated files but it may take a while. Make sure to exclude all collections from the scene (the checkbox in the outliner, not the TV or the eyeball or the camera) to make the script run as fast as possible

### Install Python Dependencies
<code>pip install -r requirements.txt</code>

## Run
<code>python.exe blender_mubin_tools.py</code>

The script will give some options and information. Make sure to build the asset library before attempting to import mubins otherwise there will be no assets to instance!

### Generated files
The asset library will be saved in the asset_library/assets folder

The blend files with imported mubins will be saved in the asset_library/ folder
- The script will name this file after the first mubin file you select

## Notes

This has only been tested with BotW for now but might work for others

many scripts in /scripts are not tested to run on their own, all are intended to be run by blender_mubin_tools.py

helper.py - runs as a script inside blender, helps with the sys path for imports

Blender plugin? Not currently


## References 
Built on parts of ArchLeaders' blender plugin 'MubinImporter' - https://github.com/ArchLeaders/MubinImporter
