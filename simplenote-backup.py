import sys
import os
import argparse
import sqlite3
import textwrap
import getpass
from os.path import expanduser, isfile
try:
    from simplenote import Simplenote
except ImportError:
    print 'simplenote.py needed for use.\nPlease run pip install simplenote'
    sys.exit(1)


def init():
    # get configuration file path
    global db_file
    db_file = expanduser("~/.config/simplenote-backup.db")
    
    # setup config directory
    config_dir = expanduser("~/.config/")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    #setup options_table
    global options_table
    options_table = "options"

    # setup notes_table
    global notes_table
    notes_table = "notes"

    # setup sqlite3 connection/cursor
    global conn, c
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
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
    c.execute("""select 1 from sqlite_master
                 where type='table' and name = ?""", [table_name])
    if c.fetchone() is not None:
        ret = True
    return ret


def createtable(table_name):
    """Creates the table given by <table_name>
       Adds a single row to the options table if it doesn't exist. """
    if table_name == options_table:
        c.execute("""create table %s
                     (username text, password text, save_directory text)"""
                  % (options_table))
        c.execute("""select count(*) from %s""" % (options_table))
        if c.fetchone() is not None:
            c.execute("""insert into %s (username, password, save_directory)
                      values(' ', ' ', ' ')""" % (options_table))
            conn.commit()
    elif table_name == notes_table:
        c.execute("""create table %s
                  (key text primary key, version integer, syncnum integer)"""
                  % (notes_table))


def parseOptions():
    parser = argparse.ArgumentParser(formatter_class=lambda prog:
                                     argparse.HelpFormatter(prog, max_help_position=80))
    parser.add_argument("-u", "--user", action="store", dest="username",
                        metavar="USERNAME", help="Simplenote Username")
    parser.add_argument("-p", "--password", action="store", dest="password",
                        metavar="PASSWORD", help="Simplenote Password")
    parser.add_argument("-d", "--directory", action="store", dest="note_dir",
                        metavar="PATH", help="Where to save notes")
    parser.add_argument("-s", "--save", action="store_true", dest="save_opts",
                        default=False,
                        help="Save entered options [default=False]")
    parser.add_argument("--delete", action="store_true", dest="dlt_opts",
                        default=False, help="Delete saved options")
    parser.add_argument("--show", action="store_true", dest="show_opts",
                        default=False, help="Show saved options")
    parser.add_argument("-v", "--verbose", action="store_true",
                        dest="verbose", default=False,
                        help="Verbose output [default=False]")
    parser.add_argument("-q", "--quiet", action="store_true",
                        dest="quiet", default=False,
                        help="Suppress all output. Ignored when --show enabled [default=False]")

    args = parser.parse_args()
    if args.save_opts:
        saveoptions(args.username, args.password, args.note_dir, args.quiet)
    if args.dlt_opts:
        dltoptions(args.quiet)
        cleanup(0)
    if args.show_opts:
        showoptions()
        cleanup(0)
    return args


def saveoptions(username, password, note_dir, quiet):
    """Save the options to the <db_file>
    """
    if not tableexists(options_table):
        createtable(options_table)
    update_required = False
    stmt = "update " + options_table + " set "
    if username is not None:
        stmt += " username = '" + username + "',"
        update_required = True
    if password is not None:
        stmt += " password = '" + password + "',"
        update_required = True
    if note_dir is not None:
        stmt += " save_directory = '" + note_dir + "'"
        update_required = True
    if update_required:
        if stmt[-1:] == ",":
            stmt = stmt[:-1]
        c.execute(stmt)
        conn.commit()
        if not quiet:
            print "Options have been saved"
    else:
        if not quiet:
            print "Nothing to save"


def showoptions():
    if tableexists(options_table):
        c.execute("""select username, password, save_directory
                     from %s """ % (options_table))
        row = c.fetchone()
        output = textwrap.dedent("""\
                 Saved options
                    username: %s
                    password: %s
                    save directory: %s """ %
                 (row["username"], row["password"], row["save_directory"]))
        print output

    else:
        print "No options to show"


def dltoptions():
    if tableexists(options_table):
        c.execute("""update %s
                     set username = ' ', password = ' ',
                     save_directory = ' '""" % (options_table))
        conn.commit()
        if not quiet:
            print "Options have been deleted"
    else:
        if not quiet:
            print "No options to delete"


def setparams(in_username, in_password, in_note_dir):
    c.execute("""select username, password, save_directory """ +
              """from """ + options_table);
    row = c.fetchone();
    
    if in_username is not None:
        username = in_username
    elif row['username'] != ' ':
        username = row['username']
    else:
        username = raw_input('Enter Simplenote Username: ')
    
    if in_password is not None:
        password = in_password
    elif row['password'] != ' ':
        password = row['password']
    else:
        password = getpass.getpass(prompt="Enter Simplenote Password: ")

    if in_note_dir is not None:
        note_dir = in_note_dir
    elif row['save_directory'] != ' ':
        note_dir = row['save_directory']
    else:
        note_dir = os.getcwd()

    return username, password, note_dir


def savenote(content, note_dir):
    """Save the current note content to the note_dir
    """
    goodchars = (' ','.',',','!','?','-','_','+','=','(',')')
    newline = content.find('\n')
    filename = content[:newline]        # should this have a maximum?
    filename = "".join(x for x in filename if x.isalnum() or x in goodchars)
    filename += '.txt'

    if not os.path.exists(note_dir):
        os.makedirs(note_dir)

    with open(os.path.join(note_dir, filename), 'w') as note_file:
        note_file.write(content)
        note_file.close()
    return filename


def logsave(key, version, syncnum):
    """Log the saved note version in db_file, notes_table
    """
    if not tableexists(notes_table):
        createtable(notes_table)
    c.execute("""insert or replace into """+notes_table+""" (key, version, syncnum)
                 values (?, ?, ?)""", (key, version, syncnum) )
    conn.commit()


def savenotes(username, password, note_dir, verbose):
    count = 0
    sn = Simplenote(username, password)
    note_list = sn.get_note_list(3)     # remove 3 after testing complete
    if note_list[1] == 0:
        for note in note_list[0]:
            if note['deleted'] == 0:
                note_object = sn.get_note(note['key'])
                if note_object[1] == 0:
                    note_content = note_object[0]['content']
                    filename = savenote(note_content, note_dir)
                    logsave(note['key'], note['version'], note['syncnum'])
                    count += 1
                    if verbose:
                        print """Note {0} version {1} saved as "{2}" """.format(note['key'], note['version'], filename)
    else:
        print "Unable to get note list. Are your credentials correct?"
        cleanup(1)
    if count > 0:
        print "{0} notes saved".format(count)


def main():
    init()
    args = parseOptions()
    username, password, note_dir = setparams(args.username, args.password, args.note_dir)
    savenotes(username, password, note_dir, args.verbose)

    cleanup(0)


if __name__ == "__main__":
    main()
