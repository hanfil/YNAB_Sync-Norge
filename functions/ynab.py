import requests
import json
import datetime
import logging

logger = logging.getLogger('YNAB_Sync')


class API:
    def __init__(self,ynab_token):
        # limit is 200 requests per hour
        self.transaction_timestamp = {}
        self.transactions = {}
        self.accounts = []
        self.payees = []
        self.credential_checkResult = False
        self.api_url = "https://api.youneedabudget.com/v1/"
        r = requests.get(url=self.api_url+"budgets", headers={'Authorization': 'Bearer '+ynab_token})
        self.update_requestsCounter()
        if r.status_code == 200:
            self.credential_checkResult = True
            self.token = ynab_token
        else:
            self.status_text = r.json()
            logger.error(r.json())
            #raise RuntimeError("YNAB || {} : {}".format(r.json()["error"]['name'], r.json()["error"]['detail']))

    def get_budget(self):
        self.update_requestsCounter()
        r = requests.get(url=self.api_url + "budgets", headers={'Authorization': 'Bearer ' + self.token})
        return r.json()['data']['budgets']

    def choose_budget(self,budgetId=None):
        if self.credential_checkResult == False:
            return "Check credentials!"

        if budgetId != None:
            self.budgetId = budgetId
            self.api_url += "budgets/"+self.budgetId+"/"
        else:
            budgets = self.get_budget()
            for i in range(len(budgets)):
                print(str(i)+': '+ budgets[i]['name'])
            budget_nr = int(input('Choose a number: '))
            while budget_nr not in range(len(budgets)):
                budget_nr = int(input('Choose a number listed: '))
            print('"'+budgets[budget_nr]['name']+'" Selected\n')
            self.budgetId = budgets[budget_nr]['id']
            self.api_url += "budgets/"+self.budgetId+"/"
            return {'id': budgets[budget_nr]['id'], 'name': budgets[budget_nr]['name']}

    def get_payees(self):
        self.update_requestsCounter()
        r = requests.get(url=self.api_url + "/payees", headers={'Authorization': 'Bearer ' + self.token})
        payees = r.json()['data']['payees']
        self.payees = payees
        return payees

    def list_accounts(self):
        if self.credential_checkResult == False:
            return "Check credentials!"
        if self.budgetId == None:
            self.choose_budget()
        self.update_requestsCounter()
        r = requests.get(url=self.api_url+"/accounts", headers={'Authorization': 'Bearer '+self.token})
        accounts = r.json()['data']['accounts']
        self.accounts = accounts
        return accounts

    def update_requestsCounter(self):
        if not 'requestCounter' in dir(self):
            self.requestCounter = 0
        if not 'requestsCounter_timer' in dir(self):
            self.requestsCounter_timer = datetime.datetime.now()
        if self.requestsCounter_timer < (datetime.datetime.now()-datetime.timedelta(hours=1)):
            self.requestCounter = 0
        self.requestCounter += 1

    def get_transactions(self, accountId, date=None, forceUpdate=False):
        # The date should be ISO formatted string (e.g. 2016-12-30)
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
            logger.info('Fetching transaction | since_date : '+date)
            self.update_requestsCounter()
            r = requests.get(url=self.api_url+"accounts/"+accountId+"/transactions",
                            headers={'Authorization': 'Bearer '+self.token},
                            params={'since_date': date})
            transactions = r.json()['data']['transactions']
            self.transactions[accountId] = transactions

        return self.transactions[accountId]

    def find_transaction(self, accountId, amount, date, clearIfFound=False, daysBack=0):
        for days in range(0, daysBack):
            new_date = (date - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            transactions = self.get_transactions(accountId, new_date)
            for transaction in transactions:
                if (transaction['amount'] / 1000) == amount:
                    if transaction['cleared'] != "cleared" and clearIfFound:
                        import json
                        logger.info('Clearing transaction: '+json.dumps(transaction))
                        self.clear_transaction(transaction['id'], transaction)
                    return transaction
        return False

    def clear_transaction(self, transactionId, transaction=None):
        if transaction == None:
            self.update_requestsCounter()
            r = requests.get(url=self.api_url+"transactions/"+transactionId,
                            headers={'Authorization': 'Bearer '+self.token})
            transaction = r.json()['data']['transaction']
        transaction['cleared'] = "cleared"
        return self.update_transaction(transaction)

    def update_transaction(self, transaction):
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
        logger.debug('Creating transaction: \n'+json.dumps(transaction))
        self.update_requestsCounter()
        r = requests.post(url=self.api_url+"transactions/",
                        headers={'Authorization': 'Bearer '+self.token,
                                'Content-Type': 'application/json'},
                        data=json.dumps({'transaction': transaction}))
        if r.status_code == 201:
            return True
        else:
            return False


class Objectify:
    """
    ## Example values
    id =  "111f11f1-1111-1111-1111-bfee1111ca11"
    date = "2019-07-02"
    amount = 1000000    # divide it by 1000 to get the true amount
    memo = "Ikea - mat"
    cleared = "cleared" | "uncleared"
    approved = true | false
    flag_color = None
    account_id = "ac1bfe1e-d111-11b1-aaed-e1c111ea1111"
    account_name = "Brukskonto - SBanken"
    payee_id = None
    payee_name = None
    category_id = "1befca1d-ef11-11b1-1a11-11e111111dc1"
    category_name = "Immediate Income SubCategory"
    transfer_account_id = None
    transfer_transaction_id = None
    matched_transaction_id = None
    import_id = None
    deleted = False
    subtransactions = []
    """
    #id, date, amount, memo, cleared, approved, flag_color, account_id, account_name, payee_id, payee_name, \
    #category_id, category_name, transfer_account_id, transfer_transaction_id, matched_transaction_id, import_id, deleted = None
    #subtransactions = []

    def __init__(self, transaction: dict):
        for k, v in transaction.items():
            setattr(self, k, v)

    def return_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'amount': self.amount,
            'memo': self.memo,
            'cleared': self.cleared,
            'approved': self.approved,
            'flag_coler': self.flag_color,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'payee_id': self.payee_id,
            'payee_name': self.payee_name,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'transfer_account_id': self.transfer_account_id,
            'transfer_transaction_id': self.transfer_transaction_id,
            'matched_transaction_id': self.matched_transaction_id,
            'import_id': self.import_id,
            'deleted': self.deleted,
            'subtransactions': self.subtransactions
        }