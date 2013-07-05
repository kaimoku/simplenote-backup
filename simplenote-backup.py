try:
    import simplenote
except ImportError:
    print 'simplenote.py needed for use.\nPlease run pip install simplenote'
    sys.exit(1)
import sys
import optparse
import sqlite3
from os.path import expanduser, isfile


def init():
    # get configuration file path
    global db_file
    db_file = expanduser("~/.config/simplenote-backup.db")
    
    #setup options_table
    global options_table
    options_table = "options"
    
    # setup sqlite3 connection/cursor
    global conn, c
    conn = sqlite3.connect(db_file)
    c = conn.cursor()


def cleanup(num):
    conn.close()
    sys.exit(num)
    

def dbexists():
    "Returns True if db_file exists"
    return isfile(db_file)


def tableexists(table_name):
    "Returns True if <table_name> exists as a table in db_file"
    ret = False
    c.execute("select 1 from sqlite_master where type='table' and name = ?", [table_name])
    if c.fetchone():
        ret = True
    return ret


def createtable(table_name):
    "Creates the table given by <table_name>"
    if table_name == options_table:
        c.execute("create table %s (username text, password text, save_directory text)" % (options_table))


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
        saveoptions()
    if options.dlt_opts:
        print "Delete the options"
        dltoptions()
        cleanup(0)
    if options.show_opts:
        print "Show the options"
        showoptions()
        cleanup(0)


def saveoptions():
    "Save the options to the <db_file>"
    if not tableexists(options_table):
        createtable(options_table)
        

def showoptions():
    if tableexists(options_table):
        print "show options"
        
    else:
        print "No options to show"


def dltoptions():
    if dbexists():
        print "delete options"
    else:
        print "no options to delete"


def main():
    init()
    parseOptions()
    
    cleanup(0)


if __name__ == "__main__":
    main()
