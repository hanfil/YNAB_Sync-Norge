import datetime, time, logging
import threading
from YSN_base import sbanken, ynab


class Process(threading.Thread):
    logger = logging.getLogger('YNAB_Sync')
 
    def __init__(self, settings):
        self.timer = 0
        self.settings = settings
        self.transactions = {}
        self.internal_transactions = []  # Transactions between accounts
        self.ynabAPI = ynab.API(self.settings['ynab_token'])
        self.ynabAPI.choose_budget(self.settings['ynab_budget']['id'])
        self.ynabAPI.get_payees()
        self.sbankToken_timer = datetime.datetime.now()
        self.sbankAPI = sbanken.API(self.settings['sbanken_customerid'], self.settings['sbanken_clientid'], self.settings['sbanken_secret'])
        if self.sbankAPI.credential_checkResult == False:
            raise RuntimeError("SBanken - Wrong Credentials!")

    def run(self,waitTime=15*60,daysBack=4):
        # waitTime is in seconds
        if self.settings.get('wait_time'):
            waitTime = int(self.settings['wait_time'])
        if self.settings.get('days_back'):
            daysBack = int(self.settings['days_back'])
        self.waitTime = waitTime
        self.daysBack = daysBack
        self.running = True
        while self.running:
            unsynchronized_transactions = self.fetch_unsynchronized_transactions()
            self.create_ynabTransactions(unsynchronized_transactions)
            self.logger.INFO('Done!')
            self.logger.INFO('Used '+str(self.ynabAPI.requestCounter)+' YNAB requests.')
            message = ('Sleeping for '+str(int(self.waitTime/60))+' minutes. You can now quit the program.')
            self.logger.INFO(message)
            self.wait()
            self.settings['ynab_budget']['startdate'] = (datetime.datetime.today() - datetime.timedelta(days=4)).strftime("%Y-%m-%d")
            if self.sbankToken_timer < (datetime.datetime.now() - datetime.timedelta(hours=1)):
                self.logger.INFO('Aquiring new oauth token from SBanken.')
                self.sbankToken_timer = datetime.datetime.now()
                self.sbankAPI = sbanken.API(self.settings['sbanken_customerid'], self.settings['sbanken_clientid'], self.settings['sbanken_secret'])
        self.logger.INFO(self.settings['name']+' | Stopping process.')
        self.running = False

    def wait(self):
        self.timer = 0
        while self.timer < self.waitTime:
            if self.running == False:
                break
            time.sleep(1)
            self.timer += 1

    def fetch_unsynchronized_transactions(self):
        unmatched_transactions = []
        for k, v in enumerate(self.settings['ynab_budget']['accounts']):
            self.logger.INFO('Checking account: '+v['name'])
            if v['to'] == "SBanken":
                self.logger.INFO('Fetching transactions from SBanken... : %s' % v['account_name'])
                sbanken_transactions = self.sbankAPI.get_transactions(v['account_linked'], startDate=self.settings['ynab_budget'].get('startdate'))
                sbanken_transactions = sbanken_transactions[::-1]
                self.transactions[v['account_linked']] = self.objectify_list(sbanken_transactions, sbanken.Objectify)

                self.logger.INFO('Fetching transactions from YNAB... : %s' % v['name'])
                ynab_transactions = self.ynabAPI.get_transactions(v['id'], date=self.settings['ynab_budget'].get('startdate'))
                self.transactions[v['id']] = self.objectify_list(ynab_transactions, ynab.Objectify)

                unmatched_transactions += self.match_olist(self.transactions[v['account_linked']], self.transactions[v['id']])

                #self.logger.INFO('Checking transactions toward YNAB...')
                #self.transaction_loop(transactions[::-1], v['id'])
        return unmatched_transactions

    def objectify_list(self, list, method) -> []:
        transformed_list = []
        for item in list:
            transformed_list.append(method(item))
        return transformed_list

    def match_olist(self, sbank_olist, ynab_olist) -> []:
        '''Returns list of unmatched sbank.objects'''
        sbank_list = sbank_olist.copy()
        ynab_list = ynab_olist.copy()
        unmatched_transactions = []
        for sbank_transaction in sbank_list:
            dayModifier = 0
            unmatched = True
            self.logger.DEBUG('looping through next ynab transaction')
            while unmatched and dayModifier <= self.daysBack:
                self.logger.DEBUG('sbank date: %s (daysback: -%s) --  amount: %s' % (sbank_transaction.accountingDate, dayModifier, sbank_transaction.amount))
                for ynab_transaction in ynab_list:
                    if sbank_transaction.compareYNAB(ynab_transaction, dayModifier):
                        if ynab_transaction.cleared == 'uncleared':
                            ynab_transaction.cleared = 'cleared'
                            self.ynabAPI.update_transaction(ynab_transaction.return_dict())
                        ynab_list.remove(ynab_transaction)
                        unmatched = False
                        break
                dayModifier += 1
            if unmatched:
                self.logger.DEBUG('Transaction unmatched.')
                if sbank_transaction.transactionTypeCode == 200:
                    self.internal_transactions.append(sbank_transaction)
                unmatched_transactions.append(sbank_transaction)
        # unclear ynab transaction which were not matched
        for ynab_transaction in ynab_list:
            ynab_transaction.cleared = 'uncleared'
            self.ynabAPI.update_transaction(ynab_transaction.return_dict())
        return unmatched_transactions

    def create_ynabTransactions(self, olist):
        self.logger.INFO('Creating YNAB transactions...')
        self.logger.INFO('Looking for internal transaction match..')
        for transaction1 in self.internal_transactions:
            for transaction2 in self.internal_transactions:
                if transaction1.accountingDate == transaction2.accountingDate:
                    if transaction1.amount + transaction2.amount == 0:
                        self.logger.DEBUG('internal transaction matched : %s' % transaction1.amount)
                        self.internal_transactions.remove(transaction1)
                        self.internal_transactions.remove(transaction2)
                        olist.remove(transaction1)
                        olist.remove(transaction2)
                        ynab_accountId1 = self.fetchYNABAccountId(transaction1.accountId)
                        ynab_accountId2 = self.fetchYNABAccountId(transaction2.accountId)
                        new_ynab_transaction = transaction1.transformToYNAB(ynab_accountId1, payee_id=self.fetchYNABPayeeId(ynab_accountId2))
                        self.ynabAPI.create_transaction(new_ynab_transaction)
        self.logger.INFO('Looking through unsynchronized transactions...')
        for item in olist:
            self.logger.INFO('creating transaction : %s %s ,-' % (item.text, item.amount))
            ynab_accountId = self.fetchYNABAccountId(item.accountId)
            self.ynabAPI.create_transaction(item.transformToYNAB(ynab_accountId))

    def fetchYNABAccountId(self, account_linked):
        '''Fetching YNAB accountId based upon linked sbank account.'''
        accounts = self.settings['ynab_budget']['accounts']
        for account in accounts:
            if account['account_linked'] == account_linked:
                return account['id']
        return None

    def fetchYNABPayeeId(self, ynab_accountId):
        payees = self.ynabAPI.payees
        for payee in payees:
            if payee['transfer_account_id'] == ynab_accountId:
                return payee['id']
        return None
