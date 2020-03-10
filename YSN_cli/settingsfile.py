import json
import logging
logger = logging.getLogger('YNAB_Sync')

def update_settings(self, settings, settingsfile):
    logger.info('>update_settings | Updating %s with current settings' % settingsfile)
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
        ynabAPI = ynab.API(settings['ynab_token'])
        while ynabAPI.credential_check == False:
            print('Wrong TOKEN!!')
            settings['ynab_token'] = input('Enter YNAB TOKEN :: https://app.youneedabudget.com/settings/developer \n')
            ynabAPI = ynab.API(settings['ynab_token'])
        print('Authorized TOKEN!\n')
        update_settings(self, settings, settingsfile)

    if settings.get('ynab_budget') == None:
        print('YNAB Budget not selected.')
        settings['ynab_budget'] = ynabAPI.choose_budget()
        update_settings(self, settings, settingsfile)

    if settings.get('sbanken_customerid') == None:
        credential_check = False
        while credential_check == False:
            settings['sbanken_customerid'] = input('Enter SBANKEN CUSTOMERID :: https://github.com/Sbanken/api-examples#faq \n')

            settings['sbanken_clientid'] = input('Enter SBANKEN CLIENTID :: https://github.com/Sbanken/api-examples#availability \n')

            settings['sbanken_secret'] = input('Enter SBANKEN SECRET :: https://github.com/Sbanken/api-examples#availability \n')

            sbankAPI = sbanken.API(settings['sbanken_customerid'], settings['sbanken_clientid'], settings['sbanken_secret'])
            credential_check = sbankAPI.credential_checkResult
        print('SBanken Authorized!\n')
        update_settings(self, settings, settingsfile)

    if settings['ynab_budget'].get('accounts') == None or len(settings['ynab_budget']['accounts']) == 0:
        print('No linked account found!')
        settings['ynab_budget']['accounts'] = []
        settings = link_accounts(settings)
        update_settings(self, settings, settingsfile)

    return settings
