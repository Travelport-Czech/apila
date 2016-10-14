
'use strict';

const assert = require('assert');
const ReservationHandler = require('./../app/ReservationHandler');

describe('Reservation create', () => {
  it('should succes put item', (done) => {
    function DocumentClientMock() {
      this.put = function(params, onDone) {
        onDone(null);
      }
    };

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'ACTIVE',
      reservationArn: 'test'
    };
    const createDateTime = new Date().toString();
    const callback = function(err) {
      assert.equal(null, err);
      done();
    };
    reservationHandler.create(reservationDetail, createDateTime, callback);
  });
});

describe('Reservation evaluate', () => {
  it('should ignore issued reservation', (done) => {
    function DocumentClientMock() {};

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'ISSUED',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal(null, err);
      assert.deepEqual({"fraud-detected": false}, data);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });

  it('should ignore unsuccessful reservation', (done) => {
    function DocumentClientMock() {};

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'UNSUCCESSFUL',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal(null, err);
      assert.deepEqual({"fraud-detected": false}, data);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });

  it('should throw exception with invalid reservation status', (done) => {
    function DocumentClientMock() {};

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'BLBOST',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal("Invalid reservation status: BLBOST", err);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });

  it('should detect fraud after second rejected reservation with same email and different partialIIN', (done) => {
    function DocumentClientMock() {
      this.query = function(params, onDone) {
        onDone(null, [{
          ipAddress: '1.2.3.4',
          email: 'pan@email.cz',
          itinerary: {},
          passengers: {},
          itineraryPassangersHash: "abcdef",
          partialIIN: '1235',
          reservationResult: 'REJECTED',
          reservationArn: 'test'
        },
        {
          ipAddress: '1.2.3.4',
          email: 'pan@email.cz',
          itinerary: {},
          passengers: {},
          itineraryPassangersHash: "abcdef",
          partialIIN: '1236',
          reservationResult: 'REJECTED',
          reservationArn: 'test'
        }]);
      }
    };

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'ACTIVE',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal(null, err);
      assert.deepEqual({"fraud-detected": true}, data);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });

  it('should not detect fraud after one rejected reservation with same email and different partialIIN', (done) => {
    function DocumentClientMock() {
      this.query = function(params, onDone) {
        onDone(null, [{
          ipAddress: '1.2.3.4',
          email: 'pan@email.cz',
          itinerary: {},
          passengers: {},
          itineraryPassangersHash: "abcdef",
          partialIIN: '1235',
          reservationResult: 'REJECTED',
          reservationArn: 'test'
        }]);
      }
    };

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'ACTIVE',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal(null, err);
      assert.deepEqual({"fraud-detected": false}, data);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });

  it('should not detect fraud after one rejected reservation with same itinerary and passengers and different partialIIN', (done) => {
    function DocumentClientMock() {
      this.query = function(params, onDone) {
        onDone(null, [{
          ipAddress: '1.2.3.4',
          email: 'pan2@email.cz',
          itinerary: {},
          passengers: {},
          itineraryPassangersHash: "abcdef",
          partialIIN: '1235',
          reservationResult: 'REJECTED',
          reservationArn: 'test'
        }]);
      }
    };

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'ACTIVE',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal(null, err);
      assert.deepEqual({"fraud-detected": false}, data);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });

  it('should detect fraud after two rejected reservation with same itinerary and passengers and different partialIIN', (done) => {
    function DocumentClientMock() {
      this.query = function(params, onDone) {
        onDone(null, [{
          ipAddress: '1.2.3.4',
          email: 'pan2@email.cz',
          itinerary: {},
          passengers: {},
          itineraryPassangersHash: "abcdef",
          partialIIN: '1235',
          reservationResult: 'REJECTED',
          reservationArn: 'test'
        },
        {
          ipAddress: '1.2.3.4',
          email: 'pan3@email.cz',
          itinerary: {},
          passengers: {},
          itineraryPassangersHash: "abcdef",
          partialIIN: '1235',
          reservationResult: 'REJECTED',
          reservationArn: 'test'
        }]);
      }
    };

    const reservationHandler = new ReservationHandler(new DocumentClientMock());

    const reservationDetail = {
      ipAddress: '1.2.3.4',
      email: 'pan@email.cz',
      itinerary: {},
      passengers: {},
      partialIIN: '1234',
      reservationResult: 'ACTIVE',
      reservationArn: 'test'
    };
    const callback = (err, data) => {
      assert.equal(null, err);
      assert.deepEqual({"fraud-detected": true}, data);
      done();
    };
    const actualDateTime = new Date().toString();
    reservationHandler.evaluate(reservationDetail, actualDateTime, callback);
  });
});
