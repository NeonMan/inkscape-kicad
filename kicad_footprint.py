'''
Inkscape to KiCAD footprint plugin.
Copyright (C) 2020  J.Luis Álvarez

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

import inkex
import cspsubdiv, cubicsuperpath, simpletransform
import sys
import time
import math

log_everything = False

def log(msg, is_warning=False):
    if log_everything or is_warning:
        sys.stderr.write("[LOG] " + str(msg) + "\n")

class KicadExportException(BaseException):
    def __init__(self, message):
        self.message = str(message)
    
    def __str__(self):
        return self.message

#KiCAD lib header and footer
kicad_header = '''(module {name} (layer F.Cu) (tedit 00000000)
  (fp_text reference REF** (at 0 0.5) (layer F.SilkS) hide
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value {name} (at 0 -0.5) (layer F.Fab) hide
    (effects (font (size 1 1) (thickness 0.15)))
  )
'''

kicad_footer = '''
)
'''


#Constants n stuff
tag_group = '{http://www.w3.org/2000/svg}g'
tag_path = '{http://www.w3.org/2000/svg}path'
attr_groupmode = '{http://www.inkscape.org/namespaces/inkscape}groupmode'
attr_label = '{http://www.inkscape.org/namespaces/inkscape}label'

polygon_header = '(fp_poly (pts '
polygon_footer = ') (layer {layer}) (width 0.1))\n'

class KicadExport(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        #Argument parser
        self.OptionParser.add_option('--layer',      action='store', type='string', dest='layer',      default='AUTO', help='Layer to use')
        self.OptionParser.add_option('--name',       action='store', type='string', dest='name',       default=None,   help='Footprint name')
        self.OptionParser.add_option('--output',     action='store', type='string', dest='output',     default=None,   help='Output file')
        self.OptionParser.add_option('--resolution', action='store', type='float',  dest='resolution', default=0.1,    help='Resolution (mm)')

        #Inkscape seems to thing a tab stack is an option... whatev. Ignore
        self.OptionParser.add_option('--tabs', action='store', type='string', dest='ignore', default="")
    def effect(self):
        #Sanity checks
        if self.getDocumentUnit() != 'mm':
            raise KicadExportException("SVG units MUST BE millimeters")
        if self.document == None:
            raise KicadExportException("Document failed to parse")
        
        #Get arguments and document info.
        doc_width = int(self.getDocumentWidth()[:-2])
        doc_height = int(self.getDocumentHeight()[:-2])
        
        out_name = self.options.name
        if (out_name == None) or (out_name == ''):
            #Generate a sorta random footprint name
            out_name = "FOOTPRINT" + str(int(time.time()))
            log("Using generated footprint name: " + out_name)
        self.out_name = out_name
        
        out_file = sys.stdout
        if (self.options.output != None):
            out_file = open(self.options.output, 'w')
        self.out_file = out_file
                
        out_layer = None
        if self.options.layer != 'AUTO':
            out_layer = self.options.layer
        self.out_layer = out_layer
            
        #Write header
        out_file.write(kicad_header.format(name=out_name))
        
        #Enumerate all SVG layers
        for element in self.document.iter(tag_group):
            #Find groups with the attribute inkscape:groupmode="layer"
            if attr_groupmode in element.attrib.keys():
                if element.attrib[attr_groupmode] == 'layer':
                    #It is a layer, get the layer name and call process_layer
                    layer_name_svg   = element.attrib[attr_label]
                    layer_name_kicad = element.attrib[attr_label]
                    if out_layer != None:
                        layer_name_kicad = out_layer
                    
                    log("Processing layer: " + layer_name_svg + " --> " + layer_name_kicad)
                    self.process_layer(element, layer_name_kicad)
        
        #Write footer
        out_file.write(kicad_footer)
        
        #Cleanup
        if out_file != sys.stdout:
            out_file.close()
    
    def get_transform_list(self, node, cummulative = []):
        #For each node, get all the 'transform' attributes up the node tree
        transform_list = cummulative
        try:
            transform_list = transform_list + [simpletransform.parseTransform(node.attrib['transform']), ]
        except KeyError as e:
            pass
        
        #If parent exists, recurse
        if node.getparent():
            transform_list = self.get_transform_list(node.getparent(), transform_list)
        return transform_list
        
    def process_layer(self, layer_element, layer_name):
        #For each layer group, get each path.

        for element in layer_element.iter(tag_path):
            log("Found path: " + str(element.attrib['d']))
            #Get the point transform at node
            svg_transforms = self.get_transform_list(element)
            #Parse path
            parsed_path = cubicsuperpath.parsePath(element.attrib['d'])
            #Convert into polyline
            cspsubdiv.cspsubdiv(parsed_path, self.options.resolution)
            #At this point, parsed_path contains a list of list of points (yes, I know)
            #so for each "path", each "subpath" we should get an array of points
            for subpath in parsed_path:
                log("  Subpath (%d points)" % len(subpath))
                #Write footprint path begining
                self.out_file.write(polygon_header)
                for point in subpath:
                    point = list(point[1])
                    for transform in svg_transforms:
                        log("Applying transform: " + str(transform))
                        simpletransform.applyTransformToPoint(transform, point)
                    log("    Point: " + str(point))
                    #transform point using self.transform matrix
                    #write individual point
                    self.out_file.write("(xy %f %f) " % (point[0], point[1]))
                self.out_file.write(polygon_footer.format(layer=layer_name))

# Create object and call affect()
if __name__ == '__main__':
    kicad_export = KicadExport()
    kicad_export.affect()
