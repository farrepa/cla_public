/* global test, createDriver, checkLayout, GalenPages, forAll */

'use strict';

var devices = {
  mobile: {
    name: 'mobile',
    size: '400x580'
  },
  tablet: {
    name: 'tablet',
    size: '1024x768'
  },
  desktop: {
    name: 'desktop',
    size: '1280x1024'
  }
};

var ProblemPage = function(driver) {
  GalenPages.extendPage(this, driver, {
    startButton: '.button-get-started',

    load: function() {
      this.startButton.click();
      return this;
    }
  });
};

forAll(devices, function() {
  test('Test problem page on ${name}', function(device) {
    var driver = createDriver('http://localhost:5000/', device.size, 'firefox');

    new ProblemPage(driver).load();

    checkLayout(driver, 'tests/galen/specs/problem-page.spec', device.name);

    driver.quit();
  });

});
