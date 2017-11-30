import sys
import boto3
from os import walk
import datetime
import time
from datetime import timedelta

def checkResponse(response):
    if response['ResponseMetadata']['HTTPStatusCode']==200:
        return True
    else:
        return False

def createDatabase(dynClient, uritablename):
    response = dynClient.create_table(
        AttributeDefinitions=[
            {
                'AttributeName':'URI',
                'AttributeType':"S"
            },
            {
                'AttributeName':'StartAndEndDate',
                'AttributeType':"S"
            }
        ],
        TableName=uritablename,
        KeySchema=[
            {
                'AttributeName': 'URI',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'StartAndEndDate',
                'KeyType': 'RANGE'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
        )

    if (checkResponse(response)):
        print ('Table {0} created'.format(uritablename))
    else:
        print ('Could not create table {0}.\n{1]}'.format(uritablename, respsonse))

def addTestRecords(dynClient, uritablename):
    while True:
        response = dynClient.describe_table(
            TableName=uritablename
            )
        if response['Table']['TableStatus'] == 'ACTIVE':
            print('Table is created and ready')
            break


    currDate = datetime.datetime.now()
    dfive = '{:%m-%d-%Y}'.format(currDate - timedelta(days=5))
    dfour = '{:%m-%d-%Y}'.format(currDate - timedelta(days=4))
    dtwenty = '{:%m-%d-%Y}'.format(currDate - timedelta(days=20))
    dfuture = '{:%m-%d-%Y}'.format(currDate + timedelta(days=30))
    dNow = '{:%m-%d-%Y %h:%m}'.format(currDate)

    records = [['/test1', dtwenty+'^'+dfive, '0', '/testpage3'],
            ['/test1', dfour+'^'+dfuture, '0', '/testpage1'],
            ['/test2', dfour+'^'+dfuture, '0', '/testpage2'],
            ['/test3', dfour+'^'+dfuture, '0', '/testpage3'],
    ]

    for i in records:
        print ('Putting record')
        #print (i)
        response = dynClient.put_item(
            TableName=uritablename,
            Item={'URI':{'S':i[0]},
            'StartAndEndDate':{'S':i[1]},
            'Count':{'N':i[2]},
            'rewrite':{'S':i[3]},
            'updatetime':{'S':dNow}
            }
            )
        if (checkResponse(response)):
            print('Record added')
        else:
            print('Error adding record\n{0}'.format(repsonse))


def createBucket(s3client, bucketname, websitehosting):

    #create the bucket
    #print ('creating bucket '+ bucketname)
    response = s3client.create_bucket(Bucket=bucketname)
    if (checkResponse(response)):
        print ('Bucket {0} created'.format(bucketname))
    else:
        print ('Could not create bucket {0}\n{1}'.format(bucketname, response))
        return

    #add default encryption
    response = s3client.put_bucket_encryption(
        Bucket=bucketname,
        ServerSideEncryptionConfiguration={
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }
            ]
        }
    )
    #print ("Encryption ")
    if (checkResponse(response)):
        print ('Encrytpion added to Bucket {0}'.format(bucketname))
    else:
        print ('Could not add encryption to bucket {0}\n{1}'.format(bucketname, response))
        return


    #turn on web hosting
    if(websitehosting):
        response = s3client.put_bucket_website(
            Bucket=bucketname,
            WebsiteConfiguration={
                'ErrorDocument': {
                    'Key': 'error.html'
                },
                'IndexDocument': {
                    'Suffix': 'index.html'
                },
            }
        )
        #print ("Hosting")
        if (checkResponse(response)):
            print ('Webhosting added to Bucket {0}'.format(bucketname))
        else:
            print ('Could not add Webhosting to bucket {0}.\n{1}'.format(bucketname, response))
            return

def copyobject(s3client, webbucket, page):

    f = open('./web assets/'+page, 'r')
    data=f.read()
    f.close()

    response = s3client.put_object(
        ACL='public-read',
        Body=data,
        Bucket=webbucket,
        Key=page,
        ContentType='text/html',
        StorageClass='STANDARD'
    )
    if (checkResponse(response)):
        print ('File {0} added to bucket {1}'.format(page, webbucket))
    else:
        print ('Could not add {0} to bucket {1}.\n{2}'.format(page, webbucket, response))
        return


def putobjects(s3client, webbucket):

    #iterate over directory and pass pages
    mypath = './web assets'
    for (dirpath, dirnames, filenames) in walk(mypath):
        break

    for f in filenames:
        copyobject(s3client, webbucket, f)

def main(args):

    #this script relies on the aws cli being installed and configured with user
    #credentials prior to being run
    #it uses [default] to set user and region - please use appropriately

    #check for parameters
    if len(args)==3:
    #we have the right number, store it off
        webbucket = args[1]
        emptybucket = args[2]
    else:
        print( 'correct usage is python {0} <webbucket> <emptybucket>'.format(args[0]) )
        sys.exit()

    #variables for the names of objects to be created
    #tablename is the only one to match the lambda@edge call
    uritablename = 'rewriteurl'

    #create the necessary clients
    s3client = boto3.client('s3')
    dynclient = boto3.client('dynamodb')

    #create the buckets first - these are dependencies for CF distro and
    #since they are in the public namespace, we want to make sure these are held for
    #the deployment
    createBucket(s3client, emptybucket, True)
    createBucket(s3client, webbucket, True)

    #for logging
    createBucket(s3client, emptybucket + "-log", False)

    print("Buckets are done")

    #put in the testing objects for the webbucket.  These can be deleted and are meant
    #to show basic functionality.
    #If you do delete/replace these items, make sure to add appropriate records to the
    #database
    putobjects(s3client, webbucket)

    print("Test files added to hosing bucket!")

    #setup the table and add records
    createDatabase(dynclient, uritablename)
    addTestRecords(dynclient, uritablename)

    print("Database created and test records added!")


main(sys.argv)
