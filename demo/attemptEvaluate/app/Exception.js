
'use strict';

function Exception(msg) {
  this.getMessage = function() {
    return msg;
  };
};

module.exports = Exception;