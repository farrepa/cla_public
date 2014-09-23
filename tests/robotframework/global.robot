*** Settings ***

Library           Selenium2Library


*** Variables ***

${PORT}           8002
${SERVER}         localhost:${PORT}
${BROWSER}        phantomjs
${LAUNCH URL}     http://${SERVER}/
${CHECKER URL}    http://${SERVER}/checker


*** Keywords ***

Open Home Page
    Open Browser                ${LAUNCH URL}  ${BROWSER}
    Set Window Size             1280  900
    Title Should Be             Civil Legal Advice
