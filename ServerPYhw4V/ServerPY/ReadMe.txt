Server starts up with py FTPServer.py [Logfile] [port]

If PORT is omitted, port 21 will be used by default

Ipv6 wasnt working on my machine so i could not implement it. (FUTURE i could try fixing IPV6)

~~~~~~~~~~~~~~~ 05.15.25 ~~~~~~~~~~~~~~~

Fixed create_root_dir() it works as expected now. The only issue is the userfile.txt has to be in /root
for validation to occur. I could try to make changes to this but for now this should be fine.

The system config can still be in the original folder since the check happens before /root is created

### ISSUE ###
Only one user can join server at a time because the default directory is changed to the first users profile
the validation file is left behind in root and the server cant access it. So I have to figure out how to
give users their own files system to "live" within. P1 -> Server Files; PX -> UserX's Files...
Maybe i have to move the code outside of the FTPServer class and inside the State class...

RESOLUTION
I put the code for making user directories inside the State class and it allowed another user to join
while the server was still running except only one can join at a time not simultaneously 
###             ###

~~~~~~~~~~~~~~~ 05.16.25 ~~~~~~~~~~~~~~~

Maybe instead of actually changing the directory we basically assign a pointer to the users directory 
so anytime they try to manipulate files it will automatically reference the path to their user directory.

~~~~~~~~~~~~~~~ 05.17.25 ~~~~~~~~~~~~~~~

Created pointer state.cwd which points to a users current working directory.
Fixed CWD and CDUP command.
Two users can now join at the same time (will have to test more to make sure directory tracking is working.