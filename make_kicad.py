import inkex
import sys

class KicadExports(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        #Argument parser
        self.OptionParser.add_option('--layer',  action='store', type='string', dest='layer',  default='AUTO',      help='Layer to use')
        self.OptionParser.add_option('--name',   action='store', type='string', dest='name',   default='Footprint', help='Footprint name')
        self.OptionParser.add_option('--output', action='store', type='string', dest='output', default=None,        help='Output file')

    def affect(self):
        (self.options, self.args) = self.OptionParser.parse_args()
        msg = "\nLayer: %s\nName: %s\nOutput: %s\n" % (self.options.layer, self.options.name, self.options.output)
        raise BaseException("Unimplemented" + msg)



# Create object and call affect()
if __name__ == '__main__':
    kicad_exports = KicadExports()
    kicad_exports.affect()
