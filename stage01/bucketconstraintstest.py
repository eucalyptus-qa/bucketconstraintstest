#!/usr/bin/env python
# Copyright (c) 2006,2007,2008 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
import getopt, sys, os
import boto
import time
from boto.exception import S3ResponseError
from optparse import OptionParser

def fail(message):
    print "[TEST_REPORT] FAILED " + message

def create_bucket(s3, bucket_name):
    """
    Create a bucket.  If the bucket already exists and you have
    access to it, no error will be returned by AWS.
    Note that bucket names are global to S3
    so you need to choose a unique name.
    """
    # First let's see if we already have a bucket of this name.
    # The lookup method will return a Bucket object if the
    # bucket exists and we have access to it or None.
    print "Looking up bucket " + bucket_name
    bucket = s3.lookup(bucket_name)
    if bucket:
        print 'Bucket (%s) already exists' % bucket_name
        return bucket
    else:
            # Let's try to create the bucket.  This will fail if
            # the bucket has already been created by someone else.
        try:
            print "Creating bucket " + bucket_name
            bucket = s3.create_bucket(bucket_name)
            print "Bucket created " + bucket_name
        except s3.provider.storage_create_error, e:
            print 'Bucket (%s) is owned by another user' % bucket_name
    return bucket

def upload_object_file(s3, bucket_name, key_name, path_to_file):
    """
    Write the contents of a local file to S3 and also store custom
    metadata with the object.
    bucket_name   The name of the S3 Bucket.
    key_name      The name of the object containing the data in S3.
    path_to_file  Fully qualified path to local file.
    """
    print "Looking up bucket " + bucket_name 
    bucket = s3.lookup(bucket_name)
    # Get a new, blank Key object from the bucket.  This Key object only
    # exists locally until we actually store data in it.
    print "Creating new key " + key_name
    key = bucket.new_key(key_name)
    print "Created new key " + str(key)
    print "Uploading file " + path_to_file
    key.set_contents_from_filename(path_to_file)
    print "File uploaded " + path_to_file
    return key

def main():
        # PARSE OPTIONS 
        parser = OptionParser()
        parser.add_option("--user1-access", dest="user1_access",
            help="Access key for user1")
        parser.add_option("--user2-access", dest="user2_access",
            help="Access key for user2")
        parser.add_option("--user1-secret", dest="user1_secret",
            help="Secret key for user2")
        parser.add_option("--user2-secret", dest="user2_secret",
            help="Secret key for user2")
        parser.add_option("-u","--url", dest="url",
            help="URL for S3/Walrus")        
        (options, args) = parser.parse_args()
        ### LOAD OPTIONS INTO LOCAL VARS
        user1_access = options.user1_access
        user2_access = options.user2_access
        user1_secret = options.user1_secret
        user2_secret = options.user2_secret
        url = options.url
        bucket_name =  "newbuck" + str(int(time.time()))
        key_name = "testfile"
        ## CREATE 2 walrus connections
        try:
            walrus_user1 = boto.connect_walrus(host=url, aws_access_key_id=user1_access, aws_secret_access_key=user1_secret,debug=0)
        except Exception, e:
            fail("Failure creating first walrus Boto conneciton: " + str(e))
        try:   
            walrus_user2 = boto.connect_walrus(host=url, aws_access_key_id=user2_access, aws_secret_access_key=user2_secret,debug=0)
        except Exception, e:
            fail("Failure creating second walrus BOTO: " + str(e))
        print "Connected to walrus successfully"
        ### CREATE A BUCKET WITH USER1
        try:
            buck1 = create_bucket(walrus_user1, bucket_name)  
        except Exception, e:
            fail("Failure creating bucket with user1: " + str(e))
            exit(1)
        ### ADD AN OBJECT TO THE BUCKET
        print "Bucket 1: " + str(buck1)
        try:
            key1 = upload_object_file(walrus_user1, bucket_name, key_name,"./dummyobj")
        except Exception, e:
            fail("Failure uploading file with user1 to walrus: " + str(e))
            exit(1)
        print "Object 1: " + str(key1)
        ### ATTACH A CANNED ACL TO THE OBJECT
        try:
            buck1 = create_bucket(walrus_user1, bucket_name)
        except Exception, e:
            fail("Failure creating bucket1: " + str(e))
            exit(1)
        print "ACL of bucket is originally: " + str(buck1.get_acl())    
        buck1.set_canned_acl('public-read')
        try:
            buck2 = walrus_user2.get_bucket(bucket_name)
            print str(buck2)
        except Exception, e:
            fail("Failure reading bucket1 after applying public_read: " + str(e))
            exit(1)
        print "ACL of bucket is now: " +  str(buck1.get_acl())
        try:
            buck1.set_canned_acl('private') 
        except Exception, e:
            fail("Failure attaching acl to bucket1: " + str(e))
            exit(1)
        print "ACL of bucket is now: " +  str(buck1.get_acl())
        print "Created object " + key_name + " in bucket " +buck1.name + " with acl " + str(buck1.get_key(key_name).get_acl())
    ### TRY TO READ WITH OTHER ACCOUNT
        try:
            buck2 = walrus_user2.get_bucket(bucket_name)
            fail("No exception caught when trying to read bucket with another user when the bucket is private ")
            exit(1)
        except Exception, e:
            print "Successfully received exception: " + str(e)
        ###public_read
        
            
      
if __name__ == "__main__":
    main()