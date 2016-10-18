
'use strict';

const AWS = require('aws-sdk');
const documentClient = new AWS.DynamoDB.DocumentClient();
const ReservationHandler = require('ReservationHandler'); 

const handler = new ReservationHandler(documentClient);

const done = function(err, res, callback) {
  callback(null, {
    statusCode: err ? '400' : '200',
    body: err ? err.message : JSON.stringify(res),
    headers: {
      'Content-Type': 'application/json',
    }
  });
};

const actualDateTime = new Date().getTime();

exports.handler = (event, context, callback) => {
    callback(null, {
      statusCode: 200,
      body: JSON.stringify({'message': 'Hello world'}),
      headers: {
        'Content-Type': 'application/json',
      }
    });
};

exports.create = (event, context, callback) => {
  handler.create(event, actualDateTime, function(err, res) {
    done(err, res, callback);
  });
};

exports.update = (event, context, callback) => {
  handler.update(event, actualDateTime, function(err, res) {
    done(err, res, callback);
  });
};

exports.evaluate = (event, context, callback) => {
  handler.evaluate(event, actualDateTime, function(err, res) {
    done(err, res, callback);
  });
};
