import tkinter
import struct
import argparse
import pathlib

GHIDRA_OFFSET = 0x80010000

TRIANGLE_EDGES = 0x80075bb0 - GHIDRA_OFFSET
SHORT_COUNT = 4536
TRIANGLE_EDGE_COUNT = int(SHORT_COUNT / 3) # triangles

TRIANGLE_VERTICES = 0x80077f20 - GHIDRA_OFFSET
TRIANGLE_VERTEX_COUNT = 948

SAFEMODE_JUMP_OFFSET = 0x800725f6 - GHIDRA_OFFSET
MAX_COLORS = 5
COLOR_OFFSETS = [
  0x80044373 - GHIDRA_OFFSET, # cerb text color
  0x80044377 - GHIDRA_OFFSET, # Safe mode
  0x8004437f - GHIDRA_OFFSET, # color 2
  0x8004437b - GHIDRA_OFFSET, # color 1
  0x80044383 - GHIDRA_OFFSET, # color 3
  0x80044387 - GHIDRA_OFFSET, # color 4 # cant use due to limits on number of tris
]
INITIAL_AND_COUNT_OFFSETS = [
  (0, 0x800725f2 - GHIDRA_OFFSET),
  (0x800725f2 - GHIDRA_OFFSET, 0x80072606 - GHIDRA_OFFSET),
  (0x80072668 - GHIDRA_OFFSET, 0x80072663 - GHIDRA_OFFSET),
  (0x8007264b - GHIDRA_OFFSET, 0x80072646 - GHIDRA_OFFSET),
  (0x80072685 - GHIDRA_OFFSET, 0x80072680 - GHIDRA_OFFSET),
]


canvas_size = 1000
center_x = canvas_size/2
center_y = canvas_size/2
point_size = 1

visual_scale = 2
flip = -1.

#colors
black="#000000"

def parse_mesh(input_file, scale):
  objects = {}
  colors = {}
  triangle_vertices = []
  triangle_edges = []
  # use waveform obj
  with open(input_file, "r") as mesh_file:
    lines = mesh_file.readlines()
    object_name = ""
    for line in lines:
      buffer = line.split(" ")
      item_type = buffer[0]
      if item_type == "o":
        # new object, update the active object
        object_name = buffer[1]
        objects[object_name] = { "vertices":[],
                                 "triangles":[],
                                 "color":object_name.split("_")[1].lower()}
        print(f"Loading {object_name}")
        if objects[object_name]["color"][0] != "#" and len(objects[object_name]["color"]) != 7:
          raise Exception(f"{object_name} with color: '{objects[object_name]['color']}' is not a valid color, expects color in the format of 'NAME_#xxxxxx'")
      elif item_type == "v":
        # item vertex
        # x
        x = float(buffer[1]) * scale * flip
        # z in blender is our y
        y = float(buffer[3]) * scale * flip
        objects[object_name]["vertices"].append([x,y])
      elif item_type == "f":
        # triangles: vertex_index/texture_index/normal_index
        # only care about vertex index
        a_edge = int(buffer[1].split("/")[0]) - 1
        b_edge = int(buffer[2].split("/")[0]) - 1
        c_edge = int(buffer[3].split("/")[0]) - 1
        objects[object_name]["triangles"].append([a_edge, b_edge, c_edge])

    # sort by color and set color indices
    color_objects = {}
    for object in objects.values():
      # dont sort vertices! everything expects them in original order
      triangle_vertices += object["vertices"]
      if object["color"] in color_objects:
        color_objects[object["color"]].append(object)
      else:
        color_objects[object["color"]] = [object]
    for color, objects in color_objects.items():
      vertex_count = 0
      triangle_count = 0
      for object in objects:
        vertex_count += len(object["vertices"])
        triangle_count += len(object["triangles"])
        triangle_edges += object["triangles"]
      colors[color] = {"vertex_count": vertex_count,
                       "triangle_count": triangle_count}

  return triangle_vertices, triangle_edges, colors

def parse_bios(input_file):
  triangle_vertices = []
  triangle_edges = []
  with open(input_file, "rb") as bios_file:
    bios_file.seek(TRIANGLE_EDGES)
    for i in range(TRIANGLE_EDGE_COUNT):
      a_edge = int.from_bytes(bios_file.read(2), byteorder='little', signed=False)
      b_edge = int.from_bytes(bios_file.read(2), byteorder='little', signed=False)
      c_edge = int.from_bytes(bios_file.read(2), byteorder='little', signed=False)
      triangle_edges.append((a_edge, b_edge, c_edge))
    bios_file.seek(TRIANGLE_VERTICES)
    for i in range(TRIANGLE_VERTEX_COUNT):
      x = int.from_bytes(bios_file.read(2), byteorder='little', signed=True)
      y = int.from_bytes(bios_file.read(2), byteorder='little', signed=True)
      triangle_vertices.append((x,y))
  return triangle_vertices, triangle_edges

def write_mesh(output_file, triangle_vertices, triangle_edges, colors):
  print(len(triangle_vertices), TRIANGLE_VERTEX_COUNT, TRIANGLE_VERTEX_COUNT - len(triangle_vertices))
  print(len(triangle_edges), TRIANGLE_EDGE_COUNT, TRIANGLE_EDGE_COUNT - len(triangle_edges))
  if (len(triangle_vertices) > TRIANGLE_VERTEX_COUNT):
    raise Exception(f'Imported mesh has {len(triangle_vertices)} vertices, only a maximum of {TRIANGLE_VERTEX_COUNT} are allowed')
  if (len(triangle_edges) > TRIANGLE_EDGE_COUNT):
    raise Exception(f'Imported mesh has {len(triangle_edges)} edges, only a maximum of {TRIANGLE_EDGE_COUNT} are allowed')
  with open(output_file, "rb+") as bios_file:
    bios_file.seek(TRIANGLE_EDGES)
    for triangle in triangle_edges:
      for vert in triangle:
        bios_file.write(struct.pack("<H", vert))
    # Fill unknown edges
    for i in range(len(triangle_edges), TRIANGLE_EDGE_COUNT):
      ## null triangles
      bios_file.write(struct.pack("<H", 0))
      bios_file.write(struct.pack("<H", 0))
      bios_file.write(struct.pack("<H", 0))
    bios_file.seek(TRIANGLE_VERTICES)
    for vertex in triangle_vertices:
      for value in vertex:
        # round the values into floats!
        bios_file.write(struct.pack("<h", round(value)))
    # Fill unknown vertices
    for i in range(len(triangle_vertices), TRIANGLE_VERTEX_COUNT):
      ## null vertices
      bios_file.write(struct.pack("<h", 0))
      bios_file.write(struct.pack("<h", 0))

    if colors:
      # do color fixups!
      if len(colors) > MAX_COLORS:
        raise Exception(f"Too many colors! Expected < {MAX_COLORS}, received {len(colors)}")
      # noop safemode skip for an additional color + simpler flow
      bios_file.seek(SAFEMODE_JUMP_OFFSET)
      bios_file.write(struct.pack("B",0x90))
      bios_file.write(struct.pack("B",0x90))
      color_index = 0
      triangle_index = 0
      for color, counts in colors.items():
        bios_file.seek(COLOR_OFFSETS[color_index])
        bios_file.write(struct.pack("<I", int(color[1:], 16)))
        print (color)
        print(hex(triangle_index), hex(counts["triangle_count"]))
        # now update initial index and count
        if INITIAL_AND_COUNT_OFFSETS[color_index][0] != 0:
          bios_file.seek(INITIAL_AND_COUNT_OFFSETS[color_index][0])
          bios_file.write(struct.pack("<I", triangle_index*3)) #3 shorts per tri
        if INITIAL_AND_COUNT_OFFSETS[color_index][1] != 0:
          bios_file.seek(INITIAL_AND_COUNT_OFFSETS[color_index][1])
          bios_file.write(struct.pack("<I", counts["triangle_count"] * 3)) #3 shorts per tri
        triangle_index += counts["triangle_count"]
        color_index += 1
      # null remaining colors
      for i in range(color_index, MAX_COLORS+1):
        # Set the counts to zero!
        bios_file.seek(INITIAL_AND_COUNT_OFFSETS[color_index][1])
        bios_file.write(struct.pack("<I", counts["triangle_count"]))

def draw_mesh(triangle_vertices, triangle_edges):
  root = tkinter.Tk()

  canvas = tkinter.Canvas(root, bg="white", height=canvas_size, width=canvas_size)

  for point in triangle_vertices:
    # draw oval as pseudo point, make sure to set the point about the center
    # also adding the point is upside down? seems odd make note of this
    canvas.create_oval(center_x - point[0] * visual_scale + point_size,
                       center_y - point[1] * visual_scale + point_size,
                       center_x - point[0] * visual_scale - point_size,
                       center_y - point[1] * visual_scale - point_size,
                       fill=black)

  # now draw the triangles
  for edge in triangle_edges:
    canvas.create_line(center_x - triangle_vertices[edge[0]][0] * visual_scale,
                       center_y - triangle_vertices[edge[0]][1] * visual_scale,
                       center_x - triangle_vertices[edge[1]][0] * visual_scale,
                       center_y - triangle_vertices[edge[1]][1] * visual_scale,
                       fill=black)
    canvas.create_line(center_x - triangle_vertices[edge[1]][0] * visual_scale,
                       center_y - triangle_vertices[edge[1]][1] * visual_scale,
                       center_x - triangle_vertices[edge[2]][0] * visual_scale,
                       center_y - triangle_vertices[edge[2]][1] * visual_scale,
                       fill=black)
    canvas.create_line(center_x - triangle_vertices[edge[2]][0] * visual_scale,
                       center_y - triangle_vertices[edge[2]][1] * visual_scale,
                       center_x - triangle_vertices[edge[0]][0] * visual_scale,
                       center_y - triangle_vertices[edge[0]][1] * visual_scale,
                       fill=black)

  canvas.pack()
  root.mainloop()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Utility for viewing cerbios splash meshes")
  parser.add_argument("input_file", help="An extracted cerbios or waveform obj file", type=pathlib.Path, nargs='?')
  input_type = parser.add_mutually_exclusive_group(required=True)
  input_type.add_argument("-b", "--bios", help="Input is Cerbios binary", action='store_true')
  input_type.add_argument("-m", "--mesh", help="Input is waveform obj file", action='store_true')
  parser.add_argument("-o", "--output-to-bios", help="Output mesh to bios file", type=pathlib.Path)
  parser.add_argument("-v", "--visualize", help="Open a tkinter window to visualize the input mesh", action='store_true')
  parser.add_argument("-s", "--mesh-scale", help="Scale factor for mesh, use the visual window to compare against cerbios logo for sizing", type=int, default=800)
  args = parser.parse_args()

  colors = {}
  if args.bios:
    # read input from bios
    triangle_vertices, triangle_edges = parse_bios(args.input_file)
  elif args.mesh:
    # read input from obj
    triangle_vertices, triangle_edges, colors = parse_mesh(args.input_file, args.mesh_scale)
  if args.output_to_bios:
    write_mesh(args.output_to_bios, triangle_vertices, triangle_edges, colors)
  if args.visualize:
    draw_mesh(triangle_vertices, triangle_edges)
