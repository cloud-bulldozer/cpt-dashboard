[Playwright Framework Docs](https://playwright.dev/python/docs/intro)

# Setup
- Installing dependencies 
    ```console
    $ pip install -r requirements.txt
    ```
- Download browser drivers for playwright
    ```console
    $ playwright install
    ```

# Run Test
- Run test 
    ```console
    $ pytest -vs --headed --base-url <http://localhost:3000>
    ```
- Generate allure report 
    ```console
    $ pytest --alluredir allure-results
    $ allure serve allure-results
    ```
    > Note: Make sure you have allure installed before you run these commands. [Installation Docs](https://allurereport.org/docs/gettingstarted-installation)
   