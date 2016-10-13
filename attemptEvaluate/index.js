'use strict;'

console.log('Loading function');

const  aws = require('aws-sdk');
const dynamodb = new aws.DynamoDB();

exports.handler = (event, context, callback) => {
      console.log('Received event:', JSON.stringify(event, null, 2));
      var creditId = event.creditId;
      dynamodb.getItem({
        "TableName": "credits",
        "Key": { "creditId" : { "S": creditId }}
      }, function (err, data) {
        if (err) {
          console.log('Error', err);
          callback('je to v haji');
        } else {
          var need_credit = event.credit;
          var have_credit = parseFloat(data.Item.balance.N);
          console.log(need_credit, have_credit, data, err);
          callback(null, 'je to Ok');
        }
      });
}
