*** Settings ***

Library           Selenium2Library

*** Variables ***

${PORT}        5000
${SERVER}      localhost:${PORT}
${BROWSER}     phantomjs
${HOME}        http://${SERVER}/


*** Keywords ***

Open Home Page
    Open Browser                ${HOME}  ${BROWSER}
    Set Window Size             1280  900
    Title Should Be             Civil Legal Advice

Heading text should be
    [arguments]     ${text}
    Element Text Should Be     css=h1    ${text}

Text should match regex
    [arguments]             ${locator}  ${regex}
    ${text} =               Get text    ${locator}
    Should match regexp     ${text}     ${regex}
