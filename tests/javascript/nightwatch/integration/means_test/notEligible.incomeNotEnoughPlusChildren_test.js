module.exports = {
  "Not eligible income w/ children (Your problem)": function (browser) {
    browser
      .deleteCookies()
      .url(browser.launch_url + '/checker')
      .assert.containsText('.PageHeader h1', 'Your problem', 'checker starts on correct page')
      .useXpath()
      .click('//*[@id="id_your_problem-category_0"]')
      .useCss()
      .submitForm('#content form');
  },
  
  "Not eligible income w/ children (Your finances start page)" : function (browser) {
    browser
      .assert.containsText('.PageHeader h1', 'Your finances', 'your problem start page contains correct title')
      .submitForm('#content form');
  },
  
  "Not eligible income w/ children (Your details)" : function (browser) {
    browser
      .assert.containsText('.PageHeader h1', 'About you', 'your details contains correct title')
      .execute(function () {
        $("input[value=0][type=radio]").click();
      })
      .submitForm('#content form');
  },
  
  "Not eligible income w/ children (Your finances - property)" : function (browser) {
    browser
      .assert.containsText('.PageHeader h1', 'Your money', 'your finances contains correct title')
      .execute(function () {
        $("input[type=number]").val(0);
      })
      .submitForm('#content form');
  },
  
  "Not eligible income w/ children (Your finances - income)" : function (browser) {
    browser
      .assert.containsText('.PageHeader h1', 'Your income', 'your income contains correct title')
      .execute(function () {
        $("input[type=number]").val(0);
        $("#id_your_income-earnings_0").val(733.01+(285.13*3));
        $("input[value=1][type=radio]").click();
        $("#id_dependants-dependants_old").val(2);
        $("#id_dependants-dependants_young").val(1);
      })
      .submitForm('#content form');
  },
  
  "Not eligible income w/ children (Your finances - expenses)" : function (browser) {
    browser
      .assert.containsText('.PageHeader h1', 'Your expenses', 'your expenses contains correct title')
      .execute(function () {
        $("input[type=number]").val(0);
      })
      .submitForm('#content form');
  },
  
  "Not eligible income Result" : function (browser) {
    browser
      .assert.containsText('.PageHeader h1', 'You are not able to get Legal Aid', 'result page contains unsuccessful title')
      .end();
  }
};
