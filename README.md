<p align="center">
      <img src="https://i.ibb.co.com/JR1rdsBG/logo.jpg" alt="Logo">
</p>

# WoTLK_MultiTool
Multifunctional retroporting tool. It automates manual, routine processes and features a number of unique features, significantly speeding up the process. Just a few clicks and you can preview how your model will look in-game.

# Features:
## ● CONVERT / AUTO TEXTURE FROM MANIFEST
Converts the model, automatically renames LOD files, edits the number of nViews, corrects GlobalSequences, corrects helmet misalignment, assigns textures, if they're scattered across folders and consolidates them into one folder, compiles skin and anim files, moves them to the patch folder, and removes junk files after exporting from wow.export. Generates a model name and icon name for insertion into the dbc table, taking into account the model type and race (if it's a helmet model).
## ● CREATE ARRAYS / KEYFRAMES
Instantly creates n-th number of blocks (Color, Bones, Textures, Transparency and others) with a specified number of Timestamps and Values. No more manually fiddling with bytes and offsets.
## ● COLOR CALCULATOR
Converts various color formats: hex# is used in graphic editors, DEC (decimal) is used in LightIntBand.dbc, HEX (hexadecimal) is used in 010Editor in the Color block. 
## ● MODEL POSITION / SCALE
Allows you to shift the model along the x, y, z axes (for example, offsetting helmets) and change the model's size. Offset and scale work with any model, even animated ones, and don't cause vertex collapse (possibly the only way to change the size of Warlock pets).
## ● PARTICLE CLONER
Full copying of particles from one model to another
## ● TEXTURE COMPONENTS
A module for working with textures. It will move all exported textures from the wow.export folder to the patch folder, with the option to automatically convert from DXT5 to Indexed (256Color). It will automatically remove extra digits from texture names.
# System requirements
Windows 10+, Python 3.13

⚠️ Note: The program is compiled using [Nuitka](https://nuitka.net/). Nuitka converts python code to C++. When exe launched, libraries are extracted to the %temp%/WoTLK_Multitool_Data folder. Some antivirus programs may falsely flag this project (False Positive) due to packing.
[VirusTotal report](https://www.virustotal.com/gui/file/079fe4264e1fde1165b49464dcf5d45022c0fcc1f95e689c5730b61660eff42a?nocache=1)
# Build command
```bash
python -m nuitka --standalone --onefile --onefile-tempdir-spec="{TEMP}/WoTLK_Multitool_Data" --windows-console-mode=disable --remove-output --include-data-files=C:\Users\User_name\PycharmProjects\WoTLK_MultiTool\ICO.ico=multitool.ico --include-package=comtypes --nofollow-import-to=comtypes.test,comtypes.gen,cv2,cryptography,numpy,tkinter,pydoc --windows-icon-from-ico=C:\Users\User_name\PycharmProjects\WoTLK_MultiTool\ICO.ico C:\User_name\PycharmProjects\WoTLK_MultiTool\WoTLK_MultiTool.py --output-dir=C:\Users\User_name\Desktop 
```

