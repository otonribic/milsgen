''' Combine 'tiles' that have been generated via MILSgen into a single hugh LDR file with all the
parts.
Scan the input folder and generate an output file accordingly.'''

# Settings

INPUT_DIR = 'output\\'
OUTPUT_FILE = 'milscombine.ldr'
STUD_OFFSET = 48  # In studs, really

# Get processing

import glob
files = glob.glob(INPUT_DIR + '*.ldr')
# Find the maximum width and height
pfiles = [file.rpartition('\\')[2] for file in files]
width = [entry[0] for entry in pfiles]
height = [int(entry[1:].partition('.')[0]) for entry in pfiles]
maxwidth = ord(max(width)) - 64
maxheight = max(height)
STUD_OFFSET *= 20

print('Found matrix', maxwidth, 'wide x', maxheight, 'high')
print('Combining...')

# Open output file
outfile = open(OUTPUT_FILE, 'w', encoding = 'utf8')
outfile.write('''0 Untitled
0 Name: milscombine.ldr
0 Author: MILSCombine
0 Unofficial Model
0 ROTATION CENTER 0 0 0 1 "Custom" 
0 ROTATION CONFIG 0 0
''')

# Iterate through tiles
for ty in range(maxheight):
    for tx in range(maxwidth):
        filename = chr(tx + 65) + str(ty + 1) + '.ldr'
        print('Processing ' + filename)

        inpfile = open(INPUT_DIR + filename, 'r', encoding = 'utf8')
        inpc = inpfile.readlines()
        inpfile.close()

        inpc = [entry.strip() for entry in inpc if entry.strip().startswith('1')]

        # Introduce offsets to coordinates
        for p in range(len(inpc)):
            part = inpc[p]
            part = part.split(' ')
            part[2] = int(part[2])
            part[4] = int(part[4])
            part[2] += STUD_OFFSET * tx
            part[4] -= STUD_OFFSET * ty
            part[2] = str(part[2])
            part[4] = str(part[4])
            part = ' '.join(part)
            outfile.write(part+'\n')

outfile.write('0\n')