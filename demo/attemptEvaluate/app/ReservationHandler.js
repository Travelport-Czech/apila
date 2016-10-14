
'use strict';

const md5 = require('md5');
const Exception = require('./Exception');

function ReservationHandler(documentClient) {
  const tableName = 'buresm_reservation';
  const statusList = {
    ACTIVE: "REJECTED",
    CANCELED: "UNSUCCESSFUL",
    DUPLICATE: "UNSUCCESSFUL",
    ISSUED: "ISSUED",
    PENDING: "REJECTED",
    PROCESSING: "REJECTED",
    REJECTED: "REJECTED",
    UNCONFIRMED: "REJECTED",
    UNSUCCESSFUL: "UNSUCCESSFUL"
  };

  const createItineraryPassengersHash = function(reservationDetail) {
    return md5(reservationDetail.itinerary.toString() + reservationDetail.passengers.toString());
  }

  this.create = (reservationDetail, createDateTime, callback) => {
    const params = {
      TableName: tableName,
      ConditionExpression: 'attribute_not_exists(reservationArn)',
      Item: {
        ipAddress: reservationDetail.ipAddress,
        email: reservationDetail.email,
        itinerary: reservationDetail.itinerary,
        passengers: reservationDetail.passengers,
        partialIIN: reservationDetail.partialIIN,
        reservationResult: reservationDetail.reservationResult,
        reservationArn: reservationDetail.reservationArn,
        createDateTime: createDateTime,
        itineraryPassangersHash: createItineraryPassengersHash(reservationDetail)
      }
    };
    documentClient.put(params, callback);
  };

  this.update = (reservationDetail, updateDateTime, callback) => {
    const params = {
      TableName: tableName,
      Key: {
        reservationArn: reservationDetail.reservationArn
      },
      UpdateExpression: "set ipAddress = :i, email=:e, itinerary=:it, passengers=:p, partialIIN=:pi, reservationResult=:r, updateDateTime=:u, itineraryPassangersHash=:h",
      ExpressionAttributeValues:{
        ":i": reservationDetail.ipAddress,
        ":e": reservationDetail.email,
        ":it": reservationDetail.itinerary,
        ":p": reservationDetail.passengers,
        ":pi": reservationDetail.partialIIN,
        ":r": reservationDetail.reservationResult,
        ":u": updateDateTime,
        ":h": createItineraryPassengersHash(reservationDetail)
      }
    };
    documentClient.update(params, callback);
  };

  const fraudDetected = function(callback) {
    callback(null, getResultObject(true));
  };

  const fraudNotDetected = function(callback) {
    callback(null, getResultObject(false));
  };

  const getResultObject = function(result) {
    return {"fraud-detected": result};
  };

  const mapReservationStatus = function(status) {
    if (statusList.hasOwnProperty(status)) {
      return statusList[status];
    } else {
      throw new Exception("Invalid reservation status: " + status.toString());
    }
  }

  const getReservationWithEmailInLast24Hours = function(email, actualDateTime, currentPartialIIN, callback) {
    //console.log("vypocteny aktualni cas: " + (actualDateTime - (1000*60*60*24)));
    const params = {
      TableName: tableName,
      IndexName: "email-createDateTime-index",
      ProjectionExpression: "reservationArn, email, itinerary, passengers, partialIIN, createDateTime",
      KeyConditionExpression: "email = :e and createDateTime > :t",
      ExpressionAttributeValues:{
        ":e": email,
        ":t": actualDateTime - (1000*60*60*24)
      }
    };
    documentClient.query(params, function(err, data) {
      processResultReservationWithEmailInLast24Hours(err, data, currentPartialIIN, callback);
    });
  }

  const processResultReservationWithEmailInLast24Hours = function(err, data, currentPartialIIN, callback) {
    var partialIINList = {};
    data.forEach(function(item, index, arr) {
      if (item.partialIIN != currentPartialIIN) {
        partialIINList[item.partialIIN] = true;
      }
    });
    if (Object.keys(partialIINList).length < 2) {
      return fraudNotDetected(callback);
    } else {
      return fraudDetected(callback);
    }
  };

  this.evaluate = function(reservationDetail, actualDateTime, callback) {
    try {
      const status = mapReservationStatus(reservationDetail.reservationResult);
      if (status == "ISSUED" || status == "UNSUCCESSFUL") {
        return fraudNotDetected(callback);
      }

      getReservationWithEmailInLast24Hours(reservationDetail.email, actualDateTime, reservationDetail.partialIIN, callback);

    } catch (err) {
      if (err instanceof Exception) {
        return callback(err.getMessage());
      } else {
        throw err;
      }
    }
  };
}

module.exports = ReservationHandler;