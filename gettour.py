#!env python

import urllib
import json
import boto
# from boto.s3.connection import Location
import config

# Some constants
role = "s3All"
stor = config.s3_root
#stor = "storage.acons.at"

debug = True

def get_temp_cred(role):
    # Constants for metadata temporary security credentials
    base = "http://169.254.169.254/latest"
    secs = "/meta-data/iam/security-credentials"

    # Retrieve the temporary credentials (by role)
    url = "%s%s/%s" % (base, secs, role)
    if debug:
        print "Retrieve credentials from %s" % url

    try:
        fp = urllib.urlopen(url)
        cred = json.load(fp)
    except Exception as e:
        if debug:
            print "Cannot retrieve temporary credentials"
            print e
            return None
        else:
            if debug:
                print "AK: ", cred["AccessKeyId"]
                print "SA: ", cred["SecretAccessKey"]
                print "TO: ", cred["Token"]
                print "Ex: ", cred["Expiration"]
            return cred

if config.on_server:
    if debug:
        print "Running on server"

    # On server we try to retrieve temporary credentials
    cred = get_temp_cred(role)

    # Create a s3 connection:
    if cred == None:
        # If no temporary credentials, try original ones
        if debug:
            print "No temporary credentials available, try with local credentials"
        conn = boto.connect_s3()
    else:
        conn = boto.connect_s3(cred["AccessKeyId"], cred["SecretAccessKey"],
                          security_token=cred["Token"])
else:
    if debug:
        print "Running on workstation"

    conn = boto.connect_s3()

# print "Buckets:"
# print conn.get_all_buckets()

# Retrieve the s3 object
buck = conn.get_bucket(stor)
# buck = conn.create_bucket(stor, location=Location.EU)
key = buck.get_key("tour1.sh")
tour = key.get_contents_as_string()
print "This is what I found:"
print tour

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
