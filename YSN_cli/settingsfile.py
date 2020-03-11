import json
import requests
from YSN_base import ynab, sbanken

def update_settings(self, settings, settingsfile):
    self.logger.info('>update_settings | Updating %s with current settings' % settingsfile)
    with open(settingsfile, 'w') as json_file:
        json.dump(settings, json_file, indent=4)

def create_or_check(self, settingsfile):
    try:
        with open(settingsfile) as json_file:
            settings = json.load(json_file)
    except:
        settings = {}

    if settings.get('name') == None:
        settings['name'] = input('Enter a name for the process/settings: ')
        update_settings(self, settings, settingsfile)

    if settings.get('ynab_token') == None:
        settings['ynab_token'] = input('Enter YNAB TOKEN :: https://app.youneedabudget.com/settings/developer \n')
        ynab_api = ynab.API(settings['ynab_token'])
        while ynab_api.credential_check_result == False:
            print('Wrong TOKEN!!')
            settings['ynab_token'] = input('Enter YNAB TOKEN :: https://app.youneedabudget.com/settings/developer \n')
            ynab_api = ynab.API(settings['ynab_token'])
        print('Authorized TOKEN!\n')
        update_settings(self, settings, settingsfile)

    if settings.get('ynab_budget') == None:
        ynab_api = ynab.API(settings['ynab_token'])
        print('YNAB Budget not selected.')
        settings['ynab_budget'] = ynab_api.choose_budget()
        update_settings(self, settings, settingsfile)

    if settings.get('sbanken_customerid') == None:
        credential_check = False
        while credential_check == False:
            settings['sbanken_customerid'] = input('Enter SBANKEN CUSTOMERID :: https://github.com/Sbanken/api-examples#faq \n')

            settings['sbanken_clientid'] = input('Enter SBANKEN CLIENTID :: https://github.com/Sbanken/api-examples#availability \n')

            settings['sbanken_secret'] = input('Enter SBANKEN SECRET :: https://github.com/Sbanken/api-examples#availability \n')

            sbank_api = sbanken.API(settings['sbanken_customerid'], settings['sbanken_clientid'], settings['sbanken_secret'])
            credential_check = sbank_api.credential_checkResult
        print('SBanken Authorized!\n')
        update_settings(self, settings, settingsfile)

    if settings['ynab_budget'].get('accounts') == None or len(settings['ynab_budget']['accounts']) == 0:
        print('No linked account found!')
        settings['ynab_budget']['accounts'] = []
        settings = link_accounts(settings)
        update_settings(self, settings, settingsfile)

    return settings

def link_accounts(settings):
    sbank_api = sbanken.API(settings['sbanken_customerid'], settings['sbanken_clientid'], settings['sbanken_secret'])
    print('Choose sbank account to link.')
    sbank_accounts = sbank_api.get_accounts()
    for i in range(len(sbank_accounts)):
        print(str(i)+': '+ sbank_accounts[i]['name'] + ' -- ' + sbank_accounts[i]['accountNumber'])
    sbank_account = -1
    while sbank_account not in range(len(sbank_accounts)):
        try:
            sbank_account = int(input('Choose a number listed: '))
        except: continue

    print('Choose YNAB account to link.')
    r = requests.get(url="https://api.youneedabudget.com/v1/budgets/"+settings['ynab_budget']['id']+"/accounts", headers={'Authorization': 'Bearer '+settings['ynab_token']})
    ynab_accounts = r.json()['data']['accounts']
    for i in range(len(ynab_accounts)):
        print(str(i)+': '+ ynab_accounts[i]['name'] + ' -- ' + ynab_accounts[i]['type'])
    ynab_account = -1
    while ynab_account not in range(len(ynab_accounts)):
        try: 
            ynab_account = int(input('Choose a number listed: '))
        except: continue

    settings['ynab_budget']['accounts'].append({'id': ynab_accounts[ynab_account]['id'], 'name': ynab_accounts[ynab_account]['name'], 'account_linked': sbank_accounts[sbank_account]['accountId'], 'account_name': sbank_accounts[sbank_account]['name'], 'to': 'SBanken'})
    return settings