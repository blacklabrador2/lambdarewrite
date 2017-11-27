exports.handler = (event, context, callback) => {

    console.log('starting');

    //setup the environment variables - unfortunately, Lambda@Edge cannot use
    //true environment varialbes
    const site = "http://awstburlrewrite.s3-website-us-east-1.amazonaws.com/";
    const error_page = "error.html";
    const camp_over_page = "campaignover.html";
    const table = "urlrewrite";

    //connect to AWS appropriate region for dynamo
    //this is done by looking at the arn in the context object
    var AWS = require("aws-sdk");

    //console.log(JSON.stringify(context));
    region = context.invokedFunctionArn.split(":")
    var reg = region[3].substring(0,7)
    console.log(reg);
    //showing how to do this for just 2 regions at this time
    reg='us-west';
    if (reg=='us-west')
    {
        AWS.config.update({region: "us-west-2"});
        console.log('using us-west-2');
    } else {
        AWS.config.update({region: "us-east-1"});
        console.log('using us-east-1');
    }

    var docClient = new AWS.DynamoDB.DocumentClient();

    //log the incoming request - useful for any troubleshooting
    //console.log('EVENT Stringified')
    //console.log(JSON.stringify(event));
    //console.log('Context Stringified');
    //console.log(JSON.stringify(context));
    //console.log('Request Stringified');
    //console.log(JSON.stringify(event.Records[0].cf.request));

    var uri = event.Records[0].cf.request.uri;
    var page = error_page;   //by default, will always redirect somewhere

    //setup params and query dynamo
    var params = {
        TableName : "rewriteurl",
        KeyConditionExpression: "#ur = :sssss",
        ExpressionAttributeNames:{
            "#ur": "URI"
        },
        ExpressionAttributeValues: {
            ":sssss":uri
        }
    };

   docClient.query(params, function(err, data) {
        if (err) {
            console.error("Unable to query. Error:", JSON.stringify(err, null, 2));
            //send back the error page
            callback(null, redirect(site + page));
        } else {
            console.log("Query succeeded.");
            if(data.Count > 0) {
                data.Items.forEach(function(item) {
                    console.log(" -", item.URI + ": " + item.rewrite);
                    var arr=item.StartAndEndDate.split("^");
                    var startDate = new Date(arr[0]);
                    var endDate = new Date(arr[1]);
                    var currDate = new Date();
                    if ((currDate >= startDate) && (currDate <= endDate)){
                        //good redirect
                        page=item.rewrite;
                        console.log('Sending Redirect: ' + page);
                        //build response and send the 302
                        callback(null, redirect(site + page));
                    }
                });
                //if we have gotten here, there is not a valid campaign
                page = camp_over_page;
                callback(null, redirect(site + page));
            } else {
                //we have no campaigns with the uri entered by the user
                //build response and send the 302
                callback(null, redirect(site + page));
            }
        }
    });

    //console.log("Page to redirect to:" + page);
    //callback(null, page);

}


function redirect (to) {
  return {
    status: '301',
    statusDescription: 'Moved Permanently',
    headers: {
      'cache-control': [{ key: 'Cache-Control',value: 'max-age=30' }],
      location: [{ key: 'Location', value: to }]
    }
  }
}
