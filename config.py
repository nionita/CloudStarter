import sys

# User specific settings:
task_root_server = "/home/ubuntu"   # on our servers
task_root_ws     = "/j/Projects"    # on our workstation

# AWS specific settings:
s3_root = "storage.acons.at"

# We say it's server if it's not on Windows
# Now we just check the version of the Python interpreter
# and if it's compiled with MSC, it's windows and that
# means: not on server
def _is_running_on_server():
    if "[MSC " in sys.version:
        return False
    else:
        return True

def _get_task_root(ons):
    if ons:
        return task_root_server
    else:
        return task_root_ws

# Computed local settings - can differ depending where we run:
on_server = _is_running_on_server()
task_root = _get_task_root(on_server)

if __name__ == "__main__":
    print "Task root = ", task_root
    print "S3 root   = ", s3_root

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
