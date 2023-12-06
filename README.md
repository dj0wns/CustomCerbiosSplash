# CustomCerbiosSplash
Utility to replace the 2.3.1 cerbios splash screen with a mesh generated in blender. Note that this removes the ability to display the "Safe Mode" text on safe mode boot.

# **Warning** #
**This program modifies logic flow in the cerbios bios and could result in a broken bios. DO NOT flash any produced bioses to TSOP unless you have a way to recover. I do not guarantee that this even works on anything other than my personal xbox. I highly recommend testing in Xemu if possible. If this bricks your xbox... sucks lol**

# What you need # 
1. An unmodified copy of Cerbios 2.3.1
2. Cerbios Tool: https://github.com/Team-Resurgent/CerbiosTool
3. A 2D mesh in a wavefront .obj file with special formatting (explained below)
4. Python 3.8 or newer
5. Blender (optional)
6. Inkscape (optional)

# Setting up Cerbios #
The script requires an unpacked cerbios file to make modifications, use the unpack.exe found within Cerbios Tool to do this.

`unpack.exe "Cerbios Hybrid V2.3.1 BETA.bin" cerbios_unpacked.bin`

# Creating a Wavefront .obj file #
**This obj file cannot have more than 5 colors, 948 vertices, or 1512 triangles!**
There are infinitely many methods for this, I am posting my method which was to draw my item in Inkscape, and then import the svg into blender, which will generate the mesh for you.

1. Draw your splash in Inkscape ![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/6eac1d0e-718a-44a8-bf16-d75fec88a276)
2. Save to an .svg
3. Import svg into Blender
4. Center drawing on the XZ plane![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/d72f6f94-fc67-45b5-8832-3c83f245c996)
5. Name shapes in Blender such that the shape is [name]_[color code] and that they are in alphabetical order, in that earlier colors get drawn first and later colors drawn later. **All objects of the same color are drawn at the same time!** ![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/f75740f3-5f3d-4f7a-af64-d067930269e2)
6. Select your shapes and export to Wavefront with the following settings: ![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/380dd7d4-e3fb-498a-ab49-152f6ae109a0)

# Using the script to import the image into cerbios #
1. Use visual mode to see the scale of the cerbios image `python modify_cerbios_splash.py -b cerbios_unpacked.bin -v` ![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/ce3eccf1-c6f7-414c-b99f-6dd731557a52)
2. Use visual mode to see your .obj file `python modify_cerbios_splash.py -m duckbios.obj -v` ![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/9a255397-f254-4ca6-974e-4e10e9c82ccf)
3. Make sure you are happy with the relative size of the drawing to the original cerbios logo. You can add `-s [value]` to change the scale, default is 800x because it worked for my drawing. ex: `python modify_cerbios_splash.py -m duckbios.obj -s 1000 -v`
4. Now patch the drawing into the unpacked cerbios `python draw_cerbios.py -m duckbios.obj -o cerbios_unpacked.bin`. Make sure to include the scale argument if you opted for a different scale!

# Repacking Cerbios #
Take the modified unpacked cerbios and run it through the pack.exe utility found within Cerbios Tool.

`pack.exe cerbios_unpacked.bin "Cerbios Hybrid V2.3.1 BETA.bin" cerbios_patched_compiled.bin`

# Flashing Cerbios #
Now you can flash the modified cerbios to your Xbox through whatever method you prefer!
![image](https://github.com/dj0wns/CustomCerbiosSplash/assets/11657504/c616ba54-f1c7-4447-974d-7e8e1f514ae8)

 
# Script Arguments #
```
usage: modify_cerbios_splash.py [-h] (-b | -m) [-o OUTPUT_TO_BIOS] [-v] [-s MESH_SCALE] [input_file]

Utility for viewing cerbios splash meshes

positional arguments:
  input_file            An extracted cerbios or waveform obj file

options:
  -h, --help            show this help message and exit
  -b, --bios            Input is Cerbios binary
  -m, --mesh            Input is waveform obj file
  -o OUTPUT_TO_BIOS, --output-to-bios OUTPUT_TO_BIOS
                        Output mesh to bios file
  -v, --visualize       Open a tkinter window to visualize the input mesh
  -s MESH_SCALE, --mesh-scale MESH_SCALE
                        Scale factor for mesh, use the visual window to compare against cerbios logo for sizing
```

