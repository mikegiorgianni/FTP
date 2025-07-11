Server starts up with py FTPServer.py [Logfile] [port]

If PORT is omitted, port 21 will be used by default

Ipv6 wasnt working on my machine so i could not implement it. (FUTURE i could try fixing IPV6)

~~~~~~~~~~~~~~~ 05.15.25 ~~~~~~~~~~~~~~~

Fixed create_root_dir() it works as expected now. The only issue is the userfile.txt has to be in /root
for validation to occur. I could try to make changes to this but for now this should be fine.

The system config can still be in the original folder since the check happens before /root is created

### ISSUE ###
$Bug001 --CLOSED
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
Two users can now join at the same time (will have to test more to make sure directory tracking is working.) $Bug001 --CLOSED


~~~~~~~~~~~~~~~ 06.24.25 ~~~~~~~~~~~~~~~

$Bug002: client side error caused by failed login --CLOSED
    Repro: if a user failed login they would be sent back to the default input prompt as expected 
    but when they tried to login again the system would skip the password prompt 
    for the client while the server would wait for the password response.
    Solution: Implemented proper handling for a failed login status
Fixed Bug002
Upgradingfrom os.path to pathlib.
Added CWD functionality that will allow the user to create a new directory if the designated directory does not exist

~~~~~~~~~~~~~~~ 06.25.25 ~~~~~~~~~~~~~~~
Broke everything again I think its client side since the server isnt even seeing the message, similar to the issue i was having before
    -changed to f-print in user_dir since you cannot concat str & path type
Refactored code to use f-print (solves the communication issues)
    -needed to use f-print and str(path) for certain cases