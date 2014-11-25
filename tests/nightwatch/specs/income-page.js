'use strict';

var util = require('util');
var common = require('../modules/common-functions');
var EMPLOYMENT_QUESTIONS = require('../modules/constants').EMPLOYMENT_QUESTIONS;

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
    ;
  },

  'Context-dependent questions for employment status': function(client) {
    EMPLOYMENT_QUESTIONS.EMPLOYED.forEach(function(item) {
      client.assert.hidden(util.format('[name="your_income-%s-amount"]', item));
      client.assert.hidden(util.format('[name="your_income-%s-interval"]', item));
    });
    client.back();
    common.setYesNoFields(client, 'is_employed', 1);
    client.submitForm('form');
    EMPLOYMENT_QUESTIONS.EMPLOYED.forEach(function(item) {
      client.assert.visible(util.format('[name="your_income-%s-amount"]', item));
      client.assert.visible(util.format('[name="your_income-%s-interval"]', item));
    });
    client.back();
    common.setYesNoFields(client, 'is_employed', 0);
    common.setYesNoFields(client, 'is_self_employed', 1);
    client.submitForm('form');
    EMPLOYMENT_QUESTIONS.EMPLOYED.forEach(function(item) {
      client.assert.visible(util.format('[name="your_income-%s-amount"]', item));
      client.assert.visible(util.format('[name="your_income-%s-interval"]', item));
    });
  },

  'Context-dependent text and questions for partner': function(client) {
    client
      .assert.doesNotContainText('body', 'Your personal income')
      .assert.doesNotContainText('body', 'This section is for any money that is paid to you personally - for example, your wages. You should record income for your partner, if you have one, in the next section.')
    ;

    // EMPLOYMENT_QUESTIONS.EMPLOYED.concat(EMPLOYMENT_QUESTIONS.COMMON).forEach(function(item) {
    //   client.assert.elementNotPresent(util.format('[name="partner_income-%s-amount"]', item));
    //   client.assert.elementNotPresent(util.format('[name="partner_income-%s-interval"]', item));
    // });

    client.back();
    common.setYesNoFields(client, 'is_self_employed', 0);
    common.setYesNoFields(client, 'have_partner', 1);
    client
      .submitForm('form')
      .assert.containsText('h1', 'You and your partner’s income and tax')
      .assert.containsText('body', 'Your personal income')
      .assert.containsText('body', 'This section is for any money that is paid to you personally - for example, your wages. You should record income for your partner, if you have one, in the next section.')
    ;
    EMPLOYMENT_QUESTIONS.COMMON.forEach(function(item) {
      client.assert.visible(util.format('[name="partner_income-%s-amount"]', item));
      client.assert.visible(util.format('[name="partner_income-%s-interval"]', item));
    });
    client.back();
    common.setYesNoFields(client, 'is_employed', 1);
    client.submitForm('form');
    EMPLOYMENT_QUESTIONS.EMPLOYED.forEach(function(item) {
      client.assert.visible(util.format('[name="partner_income-%s-amount"]', item));
      client.assert.visible(util.format('[name="partner_income-%s-interval"]', item));
    });
  },

  'Test validation': function(client) {
    client
      .submitForm('form')
      .assert.urlContains('/outgoings')
      .back()
    ;
    ['your', 'partner'].forEach(function(person) {
      EMPLOYMENT_QUESTIONS.EMPLOYED.concat(EMPLOYMENT_QUESTIONS.COMMON).forEach(function(item) {
        client.setValue(util.format('[name=%s_income-%s-amount]', person, item), '250');
        common.submitAndCheckForFieldError(client, util.format('%s_income-%s-amount', person, item), 'Please select an interval');
        client.clearValue(util.format('[name=%s_income-%s-amount]', person, item));
        client.pause(1000);
        client.setValue(util.format('[name=%s_income-%s-interval]', person, item), 'per week');
        client.pause(1000);
        client.setValue(util.format('[name=%s_income-%s-interval]', person, item), 'per month');
        client.pause(1000);
        client.setValue(util.format('[name=%s_income-%s-interval]', person, item), 'per week');
        client.pause(1000);
        client.setValue(util.format('[name=%s_income-%s-interval]', person, item), 'per month');
        client.click('body');
        client.pause(3000);
        common.submitAndCheckForFieldError(client, util.format('%s_income-%s-interval', person, item), 'Not a valid amount');
      });
    });
  },

  'end': function(client){
    client.end();
  }

};
