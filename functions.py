class YNAB_api:
    def __init__(self,ynab_token):
        # limit is 200 requests per hour
        self.transaction_timestamp = {}
        self.transactions = {}
        import requests
        self.credential_checkResult = False
        self.api_url = "https://api.youneedabudget.com/v1/"
        r = requests.get(url=self.api_url+"budgets", headers={'Authorization': 'Bearer '+ynab_token})
        self.update_requestsCounter()
        if r.status_code == 200:
            self.credential_checkResult = True
            self.token = ynab_token
        else:
            print(r.json())
            raise RuntimeError("YNAB || {} : {}".format(r.json()["error"]['name'], r.json()["error"]['detail']))

    def choose_budget(self,budgetId=None):
        if self.credential_checkResult == False:
            return "Check credentials!"

        if budgetId != None:
            self.budgetId = budgetId
            self.api_url += "budgets/"+self.budgetId+"/"
        else:
            import requests
            self.update_requestsCounter()
            r = requests.get(url=self.api_url+"budgets", headers={'Authorization': 'Bearer '+self.token})
            budgets = r.json()['data']['budgets']
            for i in range(len(budgets)):
                print(str(i)+': '+ budgets[i]['name'])
            budget_nr = int(input('Choose a number: '))
            while budget_nr not in range(len(budgets)):
                budget_nr = int(input('Choose a number listed: '))
            print('"'+budgets[budget_nr]['name']+'" Selected\n')
            self.budgetId = budgets[budget_nr]['id']
            self.api_url += "budgets/"+self.budgetId+"/"
            return {'id': budgets[budget_nr]['id'], 'name': budgets[budget_nr]['name']}

    def list_accounts(self):
        if self.credential_checkResult == False:
            return "Check credentials!"
        if self.budgetId == None:
            self.choose_budget()
        import requests
        self.update_requestsCounter()
        r = requests.get(url=self.api_url+"/accounts", headers={'Authorization': 'Bearer '+self.token})
        accounts = r.json()['data']['accounts']
        return accounts

    def update_requestsCounter(self):
        import datetime
        if not 'requestCounter' in dir(self):
            self.requestCounter = 0
        if not 'requestsCounter_timer' in dir(self):
            self.requestsCounter_timer = datetime.datetime.now()
        if self.requestsCounter_timer < (datetime.datetime.now()-datetime.timedelta(hours=1)):
            self.requestCounter = 0
        self.requestCounter += 1

    def get_transaction(self, accountId, date=None, forceUpdate=False):
        # The date should be ISO formatted string (e.g. 2016-12-30)
        import datetime
        import logging
        if self.transaction_timestamp.get(accountId) == None or forceUpdate == True:
            self.transaction_timestamp[accountId] = datetime.datetime.now()-datetime.timedelta(minutes=1)
        if date != None and self.transactions.get(accountId) != None:
            dateFound = False
            for transaction in self.transactions[accountId]:
                if transaction['date'] <= date:
                    dateFound = True
                    break
            if not dateFound:
                self.transaction_timestamp[accountId] = datetime.datetime.now()-datetime.timedelta(minutes=1)
        if self.transaction_timestamp[accountId] < datetime.datetime.now()-datetime.timedelta(minutes=1):
            self.transaction_timestamp[accountId] = datetime.datetime.now()
            logging.info('Fetching transaction | since_date : '+date)
            import requests
            self.update_requestsCounter()
            r = requests.get(url=self.api_url+"accounts/"+accountId+"/transactions",
                            headers={'Authorization': 'Bearer '+self.token},
                            params={'since_date': date})
            transactions = r.json()['data']['transactions']
            self.transactions[accountId] = transactions

        return self.transactions[accountId]

    def find_transaction(self, accountId, amount, date, clearIfFound=False, daysBack=0):
        import logging
        import datetime
        for days in range(0, daysBack):
            new_date = (date - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            transactions = self.get_transaction(accountId, new_date)
            for transaction in transactions:
                if (transaction['amount'] / 1000) == amount:
                    if transaction['cleared'] != "cleared" and clearIfFound:
                        import json
                        logging.info('Clearing transaction: '+json.dumps(transaction))
                        self.clear_transaction(transaction['id'], transaction)
                    return transaction
        return False

    def clear_transaction(self, transactionId, transaction=None):
        if transaction == None:
            import requests
            self.update_requestsCounter()
            r = requests.get(url=self.api_url+"transactions/"+transactionId,
                            headers={'Authorization': 'Bearer '+self.token})
            transaction = r.json()['data']['transaction']
        transaction['cleared'] = "cleared"
        return self.update_transaction(transaction)

    def update_transaction(self, transaction):
        import json
        import requests
        self.update_requestsCounter()
        r = requests.put(url=self.api_url+"transactions/"+transaction['id'],
                        headers={'Authorization': 'Bearer '+self.token,
                                'Content-Type': 'application/json'},
                        data=json.dumps({'transaction': transaction}))
        if r.status_code == 200:
            return True
        else:
            return False

    def create_transaction(self, transaction):
        import json
        import requests
        import logging
        logging.info('Creating transaction: \n'+json.dumps(transaction))
        self.update_requestsCounter()
        r = requests.post(url=self.api_url+"transactions/",
                        headers={'Authorization': 'Bearer '+self.token,
                                'Content-Type': 'application/json'},
                        data=json.dumps({'transaction': transaction}))
        if r.status_code == 201:
            return True
        else:
            return False

class Sbanken_api:
    import requests

    def __init__(self, customerid, clientid, secret):
        self.credential_checkResult = False
        self.credential_check(customerid, clientid, secret)
        if self.credential_checkResult == False:
            print('Wrong Credentials')
        else:
            self.customerid = customerid
            self.clientid = clientid
            self.secret = secret

    def credential_check(self, customerid, clientid, secret):
        self.customerid = customerid
        #self.create_authenticated_http_session(clientid,secret)
        #self.get_accounts()
        try: self.create_authenticated_http_session(clientid,secret)
        except: return False
        try: self.get_accounts()
        except: return False
        self.credential_checkResult = True

    def create_authenticated_http_session(self, client_id, client_secret) -> requests.Session:
        from oauthlib.oauth2 import BackendApplicationClient
        from requests_oauthlib import OAuth2Session
        import urllib.parse
        import pprint
        oauth2_client = BackendApplicationClient(client_id=urllib.parse.quote(client_id))
        session = OAuth2Session(client=oauth2_client)
        session.fetch_token(
            token_url='https://auth.sbanken.no/identityserver/connect/token',
            client_id=urllib.parse.quote(client_id),
            client_secret=urllib.parse.quote(client_secret)
        )
        self.http_session = session

    def get_customer_information(self, customerid):
        response_object = self.http_session.get(
            "https://api.sbanken.no/exec.customers/api/v1/Customers",
            headers={'customerId': customerid}
        )
        if response_object.status_code in [401,403]:
            print(response_object)
            #print(response_object.text)
            raise RuntimeError("SBank returned:: Unauthorized "+str(response_object.status_code))
        else:
            response = response_object.json()
            #print(respone)
            if not response["isError"]:
                return response["item"]
            else:
                raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))

    def get_accounts(self):
        response = self.http_session.get(
            "https://api.sbanken.no/exec.bank/api/v1/Accounts",
            headers={'customerId': self.customerid}
        ).json()

        if not response["isError"]:
            return response["items"]
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))

    def get_transactions(self, accountId, startDate=None):
        if self.credential_checkResult == False:
            return "Check credentials!"
        if startDate == None:
            import datetime
            startDate = (datetime.datetime.today()-datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            print(startDate)
        response = self.http_session.get(
            "https://api.sbanken.no/exec.bank/api/v1/Transactions/"+accountId,
            headers={'customerId': self.customerid},
            params={'startDate': startDate}
        ).json()
        if not response["isError"]:
            return response["items"]
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))

class Sync_process:
    def __init__(self, settings):
        import datetime
        self.settings = settings
        self.ynabAPI = YNAB_api(self.settings['ynab_token'])
        self.ynabAPI.choose_budget(self.settings['ynab_budget']['id'])
        self.sbankToken_timer = datetime.datetime.now()
        self.sbankAPI = Sbanken_api(self.settings['sbanken_customerid'], self.settings['sbanken_clientid'], self.settings['sbanken_secret'])
        if self.sbankAPI.credential_checkResult == False:
            raise RuntimeError("SBanken - Wrong Credentials!")

    def main_loop(self,waitTime=15*60,daysBack=4):
        # Start main_loop in a thread, after initialising object
        # waitTime is in seconds
        import logging
        import datetime
        import time
        if self.settings.get('wait_time'):
            waitTime = self.settings['wait_Time']
        if self.settings.get('days_back'):
            daysBack = self.settings['days_back']
        self.waitTime = waitTime
        self.daysBack = daysBack
        self.run = True
        while self.run:
            self.account_loop()
            logging.info('Used '+str(self.ynabAPI.requestCounter)+' YNAB requests.')
            message=('Sleeping for '+str(int(self.waitTime/60))+' minutes. You can quit the program with Ctrl+C.')
            logging.info(message)
            self.wait()
            if self.sbankToken_timer < (datetime.datetime.now() - datetime.timedelta(hours=1)):
                logging.info('Aquiring new oauth token from SBanken.')
                self.sbankToken_timer = datetime.datetime.now()
                self.sbankAPI = Sbanken_api(self.settings['sbanken_customerid'], self.settings['sbanken_clientid'], self.settings['sbanken_secret'])
        logging.info(self.settings['name']+' | Stopping process.')

    def wait(self):
        import time
        timer = 0
        while timer < self.waitTime:
            if self.run == False:
                break
            time.sleep(1)
            timer += 1

    def account_loop(self):
        import logging
        for k,v in enumerate(self.settings['ynab_budget']['accounts']):
            logging.info('Checking account: '+v['name'])
            if v['to'] == "SBanken":
                logging.info('Fetching transactions from SBanken...')
                transactions = self.sbankAPI.get_transactions(v['account_linked'],startDate=self.settings['ynab_budget'].get('startdate'))
                logging.info('Checking transactions toward YNAB...')
                self.transaction_loop(transactions[::-1], v['id'])
                logging.info('Done!')

    def transaction_loop(self, transactions, ynab_accountId):
        import datetime
        for transaction in transactions:
            accountingDate = datetime.datetime.strptime(transaction['accountingDate'].split('T')[0],'%Y-%m-%d')
            if transaction['isReservation'] == True:
                clearIfFound=False
            else:
                clearIfFound=True
            if self.ynabAPI.find_transaction(ynab_accountId, transaction['amount'], accountingDate, clearIfFound=clearIfFound, daysBack=self.daysBack) == False:
                print(transaction)
                ynab_transaction = {
                    'date' : transaction['accountingDate'].split('T')[0],
                    'amount' : int(transaction['amount'] * 1000),
                    'memo' : (transaction['transactionType']+" - "+transaction['text']),
                    'account_id' : ynab_accountId,
                    'cleared' : 'cleared',
                    'approved' : False
                }
                if transaction['isReservation'] == True:
                    ynab_transaction['cleared'] = 'uncleared'
                self.ynabAPI.create_transaction(ynab_transaction)
