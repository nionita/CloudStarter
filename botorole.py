import boto
import urllib
import json
import time

class TempCredentials:
    # Constants for metadata temporary security credentials
    base = "http://169.254.169.254/latest"
    secs = "/meta-data/iam/security-credentials"

    def __init__(self, role=None):
        # Here: when the role is not explicitely given, it
        # will be choosen from the directory $base/$secs
        # (which should contain only one role)
        # If the role is given (from a previously credential)
        # then the operation is faster (less urlopen)
        # A few operations here could throw a lot of exceptions
        # and will have to be catched in the caller
        if not role:
            # retrieve the role as the unique file under url1:
            url = base + secs
            fp = urllib.urlopen(url)
            rolec = json.load(fp)
            role = rolec[0]

        url = base + secs + "/" + role

        # Retrieve the temporary credentials
        fp = urllib.urlopen(url)
        cred = json.load(fp)

        self.role            = role
        self.accessKeyId     = cred["AccessKeyId"]
        self.secretAccessKey = cred["SecretAccessKey"]
        self.token           = cred["Token"]
        self.expiration      = cred["Expiration"]

    def get_expiration_time(self):
        ...

# We use a few boto objects as resources over and over again
# so we pack them together in a dictionary and give it as a
# parameter to all functions that could need some of them
class botoResources:
    def __init__(self, regionName = None, reqQueueName = None,
                     resQueueName = None, bucketName = None):
        try:
            tc = TempCredentials()
        except Exception e:
            tc = None
        ti = time.time()
        self._tmpcred = tc
        self._cretime = ti
        if tc:
            self._exptime = tc.expiration
            self.S3Connection
                = boto.s3.connection.S3Connection(aws_access_key_id=tc.accessKeyId,
                    aws_secret_access_key=tc.secretAccessKey, security_token=tc.rc.token)
            self.SQSConnection
                = boto.sqs.connection.SQSConnection(aws_access_key_id=tc.accessKeyId,
                    aws_secret_access_key=tc.secretAccessKey, region=regionName,
                    security_token=tc.rc.token)
        else:
            self._exptime = None
            self.S3Connection = boto.s3.connection.S3Connection()
            self.SQSConnection = boto.sqs.connection.SQSConnection(region=regionName)
        self.reqQueue = self.SQSConnection.lookup(reqQueueName)
        self.resQueue = self.SQSConnection.lookup(resQueueName)
        self.bucket   = self.S3Connection.get_bucket(bucketName)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
