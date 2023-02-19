'''
Generate MILS tiles from given pictures constrained by multiplex of 32 in dimensions (or some
other size specified, such as 48)

Perhaps: do the entire waterfall, with every 1x1 column having a top value, and a bottom
value at the sea-level. Then raise the bottom value until it gets exposed by any full side
and then go back by 1, or until only two layers are left.

---

V2
Start from top, then at each layer, find the points that need to be supported by the underlayer
- typically those that are at the corners and the edges. Then at the next layer, combine those
that need to be supported, with those that are natural at that level (probably a union) and
check if there are any new that need attention. If e.g. there is nothing in the current layer
to support required points, just exted them one layer further downward. That is, when the
steepness is higher than 1 plate/stud.

Plates

1x1,2x1,4x1,6x1,8x1,2x2,4x2,6x2,8x2,4x4,6x4,8x4,6x6,16x6,6x16
'''

# Imports and constants

from PIL import Image as pil
import glob, os

# MASTER OFFSET & GEOMETRY
masterscale = (20, -8, -20)
masteroffset = (-15.5, -1, -16)
masteroffset = (0, 0, 0)

# plates: Xsize, Ysize, file
# DEFINE PLATES
plates = [[1, 1, '3024.DAT'], [2, 1, '3023.DAT'], [3, 1, '3623.DAT'], [4, 1, '3710.DAT'], [6, 1, '3666.DAT'], [8, 1, '3460.DAT']]
plates += [[2, 2, '3022.DAT'], [3, 2, '3021.DAT'], [4, 2, '3020.DAT'], [6, 2, '3795.DAT'], [8, 2, '3034.DAT'], [12, 2, '2445.DAT']]
plates += [[4, 4, '3031.DAT'], [6, 4, '3032.DAT'], [8, 4, '3035.DAT']]
plates += [[6, 6, '3958.DAT'], [12, 6, '3028.DAT'], [16, 6, '3027.DAT']]
plates += [[16, 16, '91405.DAT']]

automode = False  # Whether to work automatically or to ask questions to the user
verbose = False  # Whether to print out everything

# Load colour equivalent list
colfile = open('colours.csv', 'r')
col = colfile.readlines()
colfile.close()
col = [colr.split(',')[3:5] for colr in col[1:]]
col = [colr for colr in col if colr[0] and colr[1]]
colpairs = [(int(colr[0]), int(colr[1])) for colr in col]
coldict = {}
for pair in colpairs:
    coldict[pair[0]] = pair[1]

# Functions

def display(area):
    for dy in range(0, basesize):
        for dx in range(0, basesize):
            print(chr(48 + area[dx][dy] % 10), end = '')
        print()

def getbin(x, y, horizontal = True):  # Return ID code for coords.
    xp = bin(x + 1)[2:]
    yp = bin(y + 1)[2:]
    xp = xp.zfill(9)
    yp = yp.zfill(9)
    if horizontal :
        for char in xp:
            yp = char + yp
        return yp
    else:
        agg = ''
        for char in yp:
            agg = char + agg
        return xp + agg

# Mash up data: sizex, sizey, datafile, area, rotated?
totalparts = 0
platedata = []
for plate in plates:
    size = plate[0] * plate[1]
    platedata.append(plate + [size] + [False])
    # X!=Y of plate? Add its rotated version
    if plate[0] != plate[1]: platedata.append([plate[1], plate[0], plate[2], size, True])
platedata.sort(key = lambda d:d[3], reverse = True)


# Load initial data

print('MilsGen 1.1, MILS LDR generator, www.legoism.info\n---')

inputfile = 'milsgen.png'
if automode == False:
    inputfile = input('Enter the input terrain image (Default: milsgen.png):')
    if inputfile == '': inputfile = 'milsgen.png'

maxheight = 24
if automode == False:
    print('Enter the highest altitude of the modules in tiles (1/3 of a brick),')
    maxheight = input('corresponding to the highest point of the image (Default: 24):')
    if maxheight == '':maxheight = '24'
    maxheight = int(maxheight) - 1

includestructure = True
if automode == False:
    struc = input('Include substructure (baseplate, Technic bricks...)? (y/n; default:y):')
    if struc.upper() == 'N': includestructure = False

basesize = 32
if automode == False:
    bpsize = input('How large baseplates to use (in studs)? (Default: 32):')
    if bpsize:
        if int(bpsize) > 0: basesize = int(bpsize)

colour = [15] * 25
if automode == False:
    col = input('Enter the target colour number or leave blank to use milsgen.colour:')
    if col:
        # Colour specified, build sandwich
        colour = [int(col)] * (maxheight + 1)
    else:
        # Load colours from file
        cfile = open('milsgen.colour', 'r')
        colour = [int(entry.strip('\n ').partition(' ')[0]) for entry in cfile.readlines()]
        cfile.close()
        colour = [coldict[c] for c in colour]



#===============================================================================
# Calculate
#===============================================================================

# Open image, find dimensions

print('Loading input image')
image = pil.open(inputfile)
print('Image size:', image.size[0], 'x', image.size[1], 'px')
tilesx = image.size[0] // basesize;tilesy = image.size[1] // basesize
print('Target:', tilesx, 'x', tilesy, 'MILS modules')

print('Calculating altitudes')
px = image.load()

# Load into standard matrix
maxalt = 0
minalt = 255
pixel = [image.size[1] * [0] for tmp in range(image.size[0])]
for cy in range(image.size[1]):
    for cx in range(image.size[0]):
        if type(px[cx, cy]) == tuple:
            val = list(px[cx, cy])
        else:
            val = [px[cx, cy]]
        val = sum(val) / len(val)
        # Update extremes
        if val > maxalt:maxalt = val
        if val < minalt:minalt = val
        pixel[cx][cy] = val

print('Altitude extents:', minalt, '-', maxalt)
bias = minalt;factor = (maxalt - minalt) / maxheight
print('Bias:', bias, ', Scale: 1 :', factor)

for cy in range(image.size[1]):
    for cx in range(image.size[0]):
        pixel[cx][cy] = round((pixel[cx][cy] - bias) / factor)
print(image.size[0] * image.size[1], 'altitudes normalized')

# Delete previous renders
print('Deleting existent tiles...')
exfiles = glob.glob('output\\*.ldr')
for file in exfiles: os.remove(file)

for tiley in range(tilesy):
    for tilex in range(tilesx):
        tilename = 'output\\' + chr(65 + tilex) + str(tiley + 1)  # Calculate master coordinates of tile
        print('---\nProcessing tile', tilename, '(coordinates', tilex, ',', tiley, ')')
        area = tilex * basesize, tiley * basesize, tilex * basesize + basesize, tiley * basesize + basesize
        print('Pixel coord. area: ' + str(area))
        print('Analyzing area')

        tile = [basesize * [0] for tmp in range(basesize)]

        parts = []  # Aggregator of parts for tiles

        for cy in range(area[1], area[3]):
            for cx in range(area[0], area[2]):
                tile[cx - area[0]][cy - area[1]] = pixel[cx][cy]

        display(tile)

        floor = [basesize * [0] for tmp in range(basesize)]

        print('Raising floor:')

        for cy in range(1, basesize - 1):
            for cx in range(1, basesize - 1):
                neigh = []
                neigh += [tile[cx - 1][cy - 1], tile[cx][cy - 1], tile[cx + 1][cy - 1]]
                neigh += [tile[cx - 1][cy], tile[cx][cy], tile[cx + 1][cy]]
                neigh += [tile[cx - 1][cy + 1], tile[cx][cy + 1], tile[cx + 1][cy + 1]]
                floor[cx][cy] = min(neigh)

        display(floor)

        print('Splitting to layers...')

        layer = [[[False] * basesize for tmp in range(basesize)] for tmpt in range(maxheight + 1)]
        for cy in range(0, basesize):
            for cx in range(0, basesize):
                for alt in range(floor[cx][cy], tile[cx][cy] + 1):
                    layer[alt][cx][cy] = True  # Build layers

        for ly in range(maxheight + 1):
            print('Layer', ly)
            if verbose: display(layer[ly])

            map = layer[ly]

            if not any([any(v) for v in map]):
                print('Empty layer, skipping')
                continue

            # Change order of layers to get nice "bricky" stability (ha!)
            if ly % 2 == 0:
                platedata.sort(key = lambda d:d[0])
            else:
                platedata.sort(key = lambda d:d[1])
            platedata.sort(key = lambda d:d[3], reverse = True)

            # Now try tiling boolmap 'map' with each plate

            plateparts = 0

            for plate in platedata:
                if not any([any(c) for c in map]): break  # Layer full, do not look any further for plates

                if verbose: print('Attempting with plate', plate[0], 'x', plate[1])

                for top in range(0, basesize + 1 - plate[1]):  # Scan through the field for valid tilings
                    for left in range(0, basesize + 1 - plate[0]):

                        scan = map[left:left + plate[0]]
                        scan = [entry[top:top + plate[1]] for entry in scan]

                        # Check if all true!
                        scan = all([all(entry) for entry in scan])
                        if scan :
                            # All true, this can be tiled!
                            if verbose: print('Plate', plate[0], 'x', plate[1], 'at', left, 'x', top)
                            plateparts += 1
                            for cleanx in range(left, left + plate[0]):  # Clear the filled area:
                                for cleany in range(top, top + plate[1]):
                                    map[cleanx][cleany] = False
                            parts.append([ly, left, top, left + plate[0] / 2, top + plate[1] / 2, plate[2], plate[4]])

            print('Filled with', plateparts, 'parts')

        print('Entire tile solved with', len(parts), 'parts')
        print('Normalizing & writing file...')

        outfile = open(tilename + '.ldr', 'w')
        outfile.write('''0 Untitled
0 Name: {0}.ldr
0 Author: MILSGen
0 Unofficial Model
0 ROTATION CENTER 0 0 0 1 "Custom" 
0 ROTATION CONFIG 0 0
'''.format(tilename))
        if includestructure:

            #===================================================================
            # SUBSTRUCTURE
            #===================================================================

            # Baseplates
            if basesize == 32:
                outfile.write('1 7 320 32 -320 1 0 0 0 1 0 0 0 1 3811.DAT\n')  # Baseplate
            elif basesize == 48:
                outfile.write('1 7 480 32 -480 1 0 0 0 1 0 0 0 1 4186.DAT\n')  # Baseplate

            # Cornerstones
            cnr = basesize * 20 - 20
            outfile.write('''1 0 20 8 -20 1 0 0 0 1 0 0 0 1 3003.DAT\n
            1 0 20 8 -{0} 1 0 0 0 1 0 0 0 1 3003.DAT
            1 0 {0} 8 -20 1 0 0 0 1 0 0 0 1 3003.DAT
            1 0 {0} 8 -{0} 1 0 0 0 1 0 0 0 1 3003.DAT
            '''.format(cnr))

            t1 = basesize * 20 - 80
            t2 = basesize * 20 - 10
            # Technic connectors
            outfile.write('''
            1 72 80 8 -10 1 0 0 0 1 0 0 0 1 3701.DAT
            1 72 {0} 8 -10 1 0 0 0 1 0 0 0 1 3701.DAT
            
            1 72 10 8 -80 0 0 -1 0 1 0 1 0 0 3701.DAT
            1 72 10 8 -{0} 0 0 -1 0 1 0 1 0 0 3701.DAT
            
            1 72 80 8 -{1} 1 0 0 0 1 0 0 0 1 3701.DAT
            1 72 {0} 8 -{1} 1 0 0 0 1 0 0 0 1 3701.DAT
            
            1 72 {1} 8 -80 0 0 -1 0 1 0 1 0 0 3701.DAT
            1 72 {1} 8 -{0} 0 0 -1 0 1 0 1 0 0 3701.DAT
            
            \n'''.format(t1, t2))



        #=======================================================================
        # PARTS
        #=======================================================================

        for pt in parts:
            ptx = (pt[3] + masteroffset[0]) * masterscale[0]
            pty = (pt[0] + masteroffset[1]) * masterscale[1]
            ptz = (pt[4] + masteroffset[2]) * masterscale[2]
            currentcol = colour[pt[0]]  # Match layer with colour from the list

            string = '1 {3} {0} {1} {2} '.format(int(ptx), int(pty), int(ptz), currentcol)

            if pt[6] == False:
                string += '1 0 0 0 1 0 0 0 1 '
            else:
                string += '0 0 -1 0 1 0 1 0 0 '

            string += pt[5]

            outfile.write(string + '\n')

        totalparts += len(parts)
        outfile.write('0\n')
        outfile.close()
        print('File done, finishing this tile')

print(totalparts, 'total parts used')
print('All done; exiting')
