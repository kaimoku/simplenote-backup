import sys
import os
import argparse
import sqlite3
import textwrap
import getpass
try:
    from simplenote import Simplenote
except ImportError:
    print 'simplenote.py needed for use.\nPlease run pip install simplenote'
    sys.exit(1)


def output(text, priority=3):
    """Output controller - there should not be any print statements anywhere
       else in this program
    """
    if priority == 1:
        print text
    elif priority == 2:
        if not quiet:
            print text
    else:
        if verbose:
            print text


def init():
    # get configuration file path
    global db_file
    db_file = os.path.expanduser("~/.config/simplenote-backup.db")

    # setup config directory
    config_dir = os.path.expanduser("~/.config/")
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
    """Returns True if db_file exists
    """
    return os.path.isfile(db_file)


def tableexists(table_name):
    """Returns True if <table_name> exists as a table in db_file
    """
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
                        default=False, help="Delete saved options and exit")
    parser.add_argument("--show", action="store_true", dest="show_opts",
                        default=False, help="Show saved options and exit")
    parser.add_argument("-v", "--verbose", action="store_true",
                        dest="verbose", default=False,
                        help="Verbose output [default=False]")
    parser.add_argument("-q", "--quiet", action="store_true",
                        dest="quiet", default=False,
                        help="""Suppress all output.
                             Ignored when --show enabled [default=False]""")
    parser.add_argument("-f", "--force", action="store_true",
                        dest="force", default=False,
                        help="""Force note save (ignore last saved
                                version number) [default=False]""")
    parser.add_argument("-c", action="store", dest="count", type=int,
                        metavar="COUNT",
                        help=argparse.SUPPRESS)  # number of notes to get

    args = parser.parse_args()
    global verbose, quiet
    verbose = args.verbose
    quiet = args.quiet
    if args.save_opts:
        saveoptions(args.username, args.password, args.note_dir)
    if args.dlt_opts:
        dltoptions(args.quiet)
        cleanup(0)
    if args.show_opts:
        showoptions()
        cleanup(0)
    return args


def saveoptions(username, password, note_dir):
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
        output("Options have been saved")
    else:
        output("Nothing to save", priority=2)


def showoptions():
    if tableexists(options_table):
        c.execute("""select username, password, save_directory
                     from %s """ % (options_table))
        row = c.fetchone()
        out = textwrap.dedent("""\
              Saved options
                 username: %s
                 password: %s
                 save directory: %s """ %
                             (row["username"], row["password"],
                              row["save_directory"]))
        output(out, priority=1)
    else:
        output("No saved options to show", priority=1)


def dltoptions():
    if tableexists(options_table):
        c.execute("""update %s
                     set username = ' ', password = ' ',
                     save_directory = ' '""" % (options_table))
        conn.commit()
        output("Options have been deleted", priority=1)
    else:
        output("No options to delete", priority=1)


def setparams(in_username, in_password, in_note_dir):
    c.execute("""select username, password, save_directory """ +
              """from """ + options_table)
    row = c.fetchone()

    if in_username is not None:
        username = in_username
    elif row['username'] != ' ':
        username = row['username']
    else:
        username = raw_input("Enter Simplenote Username: ")

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


def newnoteversion(key, version):
    """Check passed note key and version against notes_table.
       Return True if passed version is greater than notes_table version
    """
    if tableexists(notes_table):
        c.execute("""select version from """+notes_table+"""
                     where key = ?""", [key])
        row = c.fetchone()
        if row is not None and row['version'] >= version:
            output("{0} version {1} not changed".format(key, version))
            return False
    return True


def savenote(content, note_dir):
    """Save the current note content to the note_dir
    """
    goodchars = (' ', '.', ',', '!', '?', '-', '_', '+', '=', '(', ')')
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
    c.execute("""insert or replace into """+notes_table+"""
                 (key, version, syncnum) values (?, ?, ?)""",
              (key, version, syncnum))
    conn.commit()


def savenotes(username, password, note_dir, num_notes, forcesave):
    count = 0
    sn = Simplenote(username, password)
    if num_notes is not None:
        output("Getting {0} notes".format(num_notes))
        note_list = sn.get_note_list(num_notes)
    else:
        output("Getting all notes")
        note_list = sn.get_note_list()
    if note_list[1] == 0:
        output("Get Note List successful")
        output("Saving notes to {0}".format(note_dir))
        for note in note_list[0]:
            if note['deleted'] == 0 and (forcesave or newnoteversion(note['key'], note['version'])):
                note_object = sn.get_note(note['key'])
                if note_object[1] == 0:
                    note_content = note_object[0]['content']
                    filename = savenote(note_content, note_dir)
                    logsave(note['key'], note['version'], note['syncnum'])
                    count += 1
                    output("Note {0} version {1} saved as '{2}'".format(note['key'], note['version'], filename))
    else:
        output("Unable to get note list. Are your credentials correct?",
               priority=1)
        cleanup(1)
    if count > 0:
        output("{0} notes saved".format(count), priority=2)


def main():
    init()
    args = parseOptions()
    username, password, note_dir = setparams(args.username, args.password,
                                             args.note_dir)
    savenotes(username, password, note_dir, args.count, args.force)
    cleanup(0)


if __name__ == "__main__":
    main()
