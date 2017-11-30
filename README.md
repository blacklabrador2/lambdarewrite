# lambdarewrite
Lambda based rewrite

SETUP
1) Copy all files from this GIT respository to a directory

2) Run the setuppucketsdy.py file (requires Python 2.7, AWS CLI, boto3 and a valid default AWS configuration to be setup)
  a) This script will create 3 buckets, following your naming scheme.  Since S3 requires unique bucket names, it is recommended 
      that you use your naming scheme to create these buckets and not something like 'rewriteurl'
  b) The script takes 2 inputs:
    i) WebBucket - this bucket is for serving the static assets out of.  It is where the function will redirect the user to.
      a) Some sample files will also be copied to this bucket from the web assets directory
      b) WebBucket-log will also be created to store any access logs for webhosting
    ii) EmptyBucket - this bucket is used to create an empty bucket for the CloudFront distribution that will be created later
  c) A Dynamo table, rewriteurl, will also be created and populated with some sample records to match the files stored in the
      WebBucket
    
3) Create a new IAM role
  a) The role needs to have trust relationships with lambda.amazonaws.com and edgelambda.amazonaws.com
  b) Assign the Policy AWSLambdaFullAccess to the role

4) Create a lambda function using the code in rewriteurl.js
  a) Create a new blank lambda function (e.g. Author from Scratch)
  b) Name the function as you like.  Make a note of this name, as it will be required for CloudFront
  c) Choose an existing role for the function and use the role you created in step 1
  d) Set the runtime to Node.js 6.10 and handler to index.handler
  e) Paste in the code from rewriteurl.js into the editor
  f) Update the region setting in line 10 to match the region you will be using
  g) Update the site constant on line 11 to be a site of your choosing
  h) Under basic settings, set memory to 128 MB and timeout to 5 seconds
  i) Save the function
  i) [Optional] Create a testevent using testevent.json message and test the function
  j) Under Actions, Publish a new version
  k) Copy the ARN of the full version of the Lambda function, including the version.  It should look like:
      arn:aws:lambda:us-east-1:<accountID>:function:URLrewrite2:1
  
5) Create the CloudFront Distribution
  a) Set Origion Domain Name to your EmptyBucket from step 2.
  b) Set Restrict Bucket Access to False
  c) Under Lambda Function Associations, add an Event for "Viewer Request" and paste in the Arn for your Lambda function,
      including the version number, in the field
  d) Set your price class to US, Canada, and Europe for inital testing
  e) Turn logging on and set the bucket to your WebBucket-log with a prefix marked for CloudFront (e.g. cloudfront/)
  f) Create the distribution
  g) You will be given a unique URL for your CloudFront distribution and the distribution may take around 15 minutes to
      complete
      
TESTING
1) Use the URL you were given for your CloudFront distribution to test
   a) No URI should redirect you to an error page
   b) /test1, /test2, /test3 should redirect you to testpage1.html, testpage2.html, and testpage3.html respectively
   c) to setup other redirects, simply add or delete records to/from the table and place an appropriate file in WebBucket
      1) URI = uri to redirect from
      2) StartAndEndDate = combined field for start/end date in MM-DD-YYYY^MM-DD-YYYY format
      3) count = 0; reserved for future use
      4) rewrite = page to rewrite url to on site for WebBucket, assumes / from the site setting in the lambda function
      5) udpdatetime = current time; reserved for future use
     
