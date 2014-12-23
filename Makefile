test:
	./nightwatch -c tests/nightwatch/local.json -t ${test}
test-chrome:
	./nightwatch -c tests/nightwatch/local.json --env chrome -t ${test}
test-firefox:
	./nightwatch -c tests/nightwatch/local.json --env firefox -t ${test}


robot-test:
	pybot -d tests/reports/robotframework/ tests/robotframework/

robot-test-chrome:
	pybot -v BROWSER:chrome -d tests/reports/robotframework/ tests/robotframework/

robot-test-firefox:
	pybot -v BROWSER:firefox -d tests/reports/robotframework/ tests/robotframework/
