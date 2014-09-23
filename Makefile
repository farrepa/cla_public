test:
	./nightwatch --config tests/javascript/nightwatch.json
test-ff:
	./nightwatch --config tests/javascript/nightwatch.json --env firefox

robo-test:
	pybot -o None -l None -r None tests/robotframework/

robo-test-chrome:
	pybot --variable BROWSER:chrome tests/robotframework/

robo-test-firefox:
	pybot --variable BROWSER:firefox tests/robotframework/
