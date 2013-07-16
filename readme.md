#simplenote-backup.py
Save Simplenote notes as text files
*****
This python (2.7) program utilizes [simplenote.py](https://github.com/mrtazz/simplenote.py) to fetch simplenote notes, and stores them as text files. It keeps track of the saved note version (as defined by Simplenote) and will only download/save the note if it has been updated.  
This came about from my desire to have a local backup of my Simplenote notes, as I had begun to use it extensively, and the need to learn Python. As such, while I have tried to follow the pep8 style guide, I no doubt have some odd-looking code here.

###Usage:
```
simplenote-backup.py [-h] [-u USERNAME] [-p PASSWORD] [-d PATH] [-s]
                            [--delete] [--show] [-v] [-q] [-f]

optional arguments:
  -h, --help                        show this help message and exit
  -u USERNAME, --user USERNAME      Simplenote Username
  -p PASSWORD, --password PASSWORD  Simplenote Password
  -d PATH, --directory PATH         Where to save notes
  -s, --save                        Save entered options [default=False]
  --delete                          Delete saved options and exit
  --show                            Show saved options and exit
  -v, --verbose                     Verbose output [default=False]
  -q, --quiet                       Suppress all output. Ignored when --show
                                    enabled [default=False]
  -f, --force                       Force note save (ignore last saved version
                                    number) [default=False]
```

###Semi-important Notes  
 - The ```--save``` option will store the Simplenote username and password as well as the save path in an sqlite table located at ~/.config/simplenote-backup.db in **plain text**. Do not save your username/password using the built-in save unless you've comfortable with that.
 - Priority order for username/password are:
     1. Command line argument
     2. Saved argument
     3. Prompted (using raw_input/getpass)
 - Priority order for note directory is:
     1. Command line argument
     2. Saved argument
     3. Current working directory (os.getcwd)
