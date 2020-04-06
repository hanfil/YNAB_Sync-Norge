import requests, datetime, logging
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import urllib.parse
from YSN_base import ynab


class API:
    logger = logging.getLogger('YNAB_Sync')

    def __init__(self, customerid, clientid, secret):
        self.logger.debug('YSN_base >sbanken | Initializing')
        self.credential_checkResult = False
        self.credential_check(customerid, clientid, secret)
        if self.credential_checkResult == False:
            self.status_text = 'Wrong Credentials'
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
        if response_object.status_code in [401, 403]:
            print(response_object)
            #print(response_object.text)
            raise RuntimeError("SBank returned:: Unauthorized "+str(response_object.status_code))
        else:
            response = response_object.json()
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
            list = response["items"]
            # Adding accountId to list for reference
            new_list = []
            for item in list:
                item['accountId'] = accountId
                new_list.append(item)
            return new_list
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))


class Objectify:
    """
    ## Example values
    accountingDate =  "2019-07-16T00:00:00+02:00"
    interestDate = "2019-07-16T00:00:00+02:00"
    otherAccountNumberSpecified = true | false
    amount = 1000.000
    text = "Overføring mellom egne kontoert"
    transactionType = "OVFNETTB"
    transactionTypeCode = 200
    transactionTypeText = "OVFNETTB"
    isReservation = true | false
    reservationType = None
    source = "Archive"
    cardDetailsSpecified = true | false
    cardDetails = {
        'cardNumber': *1111,
        'currencyAmount': 100.000,
        'currencyRate': 1.00000,
        'merchantCategoryCode': 7523,
        'merchantCategoryDescription': "Parkering, garasje",
        'merchantCity': "HAMAR",
        'merchantName': "BANE NOR SF",
        'originalCurrencyCode': "NOK",
        'purchaseDate': "2019-07-15T00:00:00+02:00",
        'transactionId': "4890000000791450"
    }
    transactionDetailSpecified = true | false
    # Help variable for future use of object
    accountId = "1111A1B111111F1C111E1111111BFEA1"
    """
    #accountingDate, interestDate, otherAccountNumberSpecified, amount, text, transactionType, transactionTypeCode, \
    #transactionTypeText, isReservation, reservationType, source, cardDetailsSpecified, transactionDetailSpecified = None
    #cardDetails = {}

    def __init__(self, transaction: dict):
        for k, v in transaction.items():
            setattr(self, k, v)

    def return_dict(self):
        dict = {
            'accountId': self.accountId,
            'accountingDate':  self.accountingDate,
            'interestDate': self.interestDate,
            'otherAccountNumberSpecified': self.otherAccountNumberSpecified,
            'amount': self.amount,
            'text': self.text,
            'transactionType': self.transactionType,
            'transactionTypeCode': self.transactionTypeCode,
            'transactionTypeText': self.transactionTypeText,
            'isReservation': self.isReservation,
            'reservationType': self.reservationType,
            'source': self.source,
            'cardDetailsSpecified': self.cardDetailsSpecified,
            'transactionDetailSpecified': self.transactionDetailSpecified
        }
        if self.cardDetailsSpecified == True:
            dict['cardDetails'] = self.cardDetails
        return dict

    def compareYNAB(self, ynab_object: ynab.Objectify, dayModifier=0) -> bool:
        accountingDate = datetime.datetime.strptime(self.accountingDate.split('T')[0], '%Y-%m-%d')
        ynab_date = datetime.datetime.strptime(ynab_object.date, '%Y-%m-%d')
        if accountingDate - datetime.timedelta(days=dayModifier) == ynab_date:
            if self.amount == ynab_object.amount/1000:
                return True
        return False

    def transformToYNAB(self, ynab_accountId, payee_id=None):
        dict = {
            'date': self.accountingDate,
            'amount': int(self.amount * 1000),
            'memo': (self.transactionType+" - "+self.text),
            'account_id': ynab_accountId,
            'cleared': 'cleared',
            'approved': False,
            'payee_id': payee_id
        }
        return dict
