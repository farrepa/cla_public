'use strict';

var util = require('util');
var common = require('../modules/common-functions');
var OUTGOINGS_QUESTIONS = require('../modules/constants').OUTGOINGS_QUESTIONS;

module.exports = {
  'Start page': common.startPage,

  'Categories of law (Your problem)': common.selectDebtCategory,

  'About you': function(client) {
    client
      .assert.urlContains('/about')
      .assert.containsText('h1', 'About you')
    ;
    common.aboutPageSetAllToNo(client);
    client.submitForm('form');
  },

  'Income': function(client) {
    client
      .assert.urlContains('/income')
      .assert.containsText('h1', 'Your income and tax')
      .submitForm('form')
    ;
  },

  'Outgoings': function(client) {
    client
      .assert.urlContains('/outgoings')
      .assert.containsText('h1', 'Your outgoings')
    ;
  },

  'Childcare fields': function(client) {
    client
      .assert.hidden('input[name="childcare-amount"]')
      .assert.hidden('input[name="childcare-interval"]')
      .back()
      .back()
    ;
    common.setYesNoFields(client, 'have_children', 1);
    client
      .setValue('input[name="num_children"]', 1)
      .submitForm('form')
    ;
    common.setYesNoFields(client, 'other_benefits', 0);
    client
      .submitForm('form')
      .submitForm('form')
      .assert.visible('input[name="childcare-amount"]')
      .assert.visible('select[name="childcare-interval"]')
    ;
  },

  'Context-dependent text for partner': function(client) {
    client
      .assert.containsText('body', 'Money you pay your landlord')
      .assert.containsText('body', 'Money you pay to an ex-partner for their living costs')
      .assert.containsText('body', 'Money you pay towards your criminal legal aid')
      .assert.containsText('body', 'Money you pay for your child to be looked after while you work or study')
      .back()
      .back()
      .back()
    ;
    common.setYesNoFields(client, 'have_partner', 1);
    common.setYesNoFields(client, 'in_dispute', 0);
    client
      .submitForm('form')
      .submitForm('form')
      .submitForm('form')
      .assert.urlContains('/outgoings')
      .assert.containsText('h1', 'You and your partner’s outgoings')
      .assert.containsText('body', 'Money you and your partner pay your landlord')
      .assert.containsText('body', 'Money you and/or your partner pay to an ex-partner for their living costs')
      .assert.containsText('body', 'Money you and/or your partner pay towards your criminal legal aid')
      .assert.containsText('body', 'Money you and your partner pay for your child to be looked after while you work or study')
    ;
  },

  'Validation': function(client) {
    OUTGOINGS_QUESTIONS.forEach(function(item) {
      client.setValue(util.format('input[name=%s-amount]', item), '500');
      common.submitAndCheckForFieldError(client, item + '-amount', 'Please select a time period from the drop down');
      client.clearValue(util.format('input[name=%s-amount]', item));
      client.setValue(util.format('select[name=%s-interval]', item), 'per month');
      common.submitAndCheckForFieldError(client, item + '-amount', 'Not a valid amount');
    });

    OUTGOINGS_QUESTIONS.forEach(function(item) {
      client.setValue(util.format('input[name=%s-amount]', item), '500');
    });
    client
      .submitForm('form')
      .assert.urlContains('/result/eligible')
    ;


    client.end();
  }

};