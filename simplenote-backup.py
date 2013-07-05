try:
    import simplenote
except ImportError:
    print 'simplenote.py needed for use.\nPlease run pip install simplenote'
    sys.exit(1)
import sys
import optparse
import sqlite3
from os.path import expanduser


def init():
    # get configuration file path
    config_file = expanduser("~/.config/simplenote-backup.db")

def dbexists():
    if os.path.isfile(path_to_file):
        try:
            open(path_to_file)
        except IOError:
            return False
    return True


def parseOptions():
    usage = "usage: %prog [options]"
    formatter = optparse.IndentedHelpFormatter(width=80, max_help_position=80)
    parser = optparse.OptionParser(usage=usage, formatter=formatter)
    parser.add_option("-u", "--user", action="store", dest="username",
                      metavar="USERNAME", help="Simplenote Username")
    parser.add_option("-p", "--password", action="store", dest="password",
                      metavar="PASSWORD", help="Simplenote Password")
    parser.add_option("-d", "--directory", action="store", dest="dir_notes",
                      metavar="PATH", help="Where to save notes")
    parser.add_option("-s", "--save", action="store_true", dest="save_opts",
                      default=False,
                      help="Save entered options [default=False]")
    parser.add_option("--delete", action="store_true", dest="dlt_opts",
                      default=False, help="Delete saved options")
    parser.add_option("--show", action="store_true", dest="show_opts",
                      default=False, help="Show saved options")

    (options, args) = parser.parse_args()
    if options.save_opts:
        print "Save the options"
    if options.dlt_opts:
        print "Delete the options"
        dltoptions()
    if options.show_opts:
        print "Show the options"
        showoptions()


def showoptions():
    if dbexists():
        print "show options"
    else:
        print "No options to show"

def main():
    init()
    parseOptions()


if __name__ == "__main__":
    main()
