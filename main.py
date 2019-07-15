#from os import environ

"""
To promote good security practice, this sample application gets credentials from
environment variables.

For convenience during development, it is sometimes preferrable to use a `.env`
file. To do so, copy the distributed file (`cp .env.dist .env`) and add your
credentials. If you use [Pipenv](https://docs.pipenv.org/), the .env file will
be loaded automatically. If not, you can use
[python-dotenv](https://github.com/theskumar/python-dotenv):

1. Install the package by running `pip install python-dotenv`.
2. Uncomment the two lines below to load the environment variables in `.env`.
"""
"""
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# This is your social security number. The same Id which is used when you log in with BankID.
CUSTOMERID = environ['CUSTOMERID']

# Get CLIENTID ('Applikasjonsnøkkel') and SECRET ('Passord') from https://secure.sbanken.no/Personal/ApiBeta/Info
CLIENTID = environ['CLIENTID']
SECRET = environ['SECRET']
"""

import os
import sys
import json
import pprint
import requests
import threading
import logging
logging.basicConfig(level=logging.INFO)
from functions import *

def create_check_settingsFile(settingsFile):
    try:
        with open(settingsFile) as json_file:
            settings = json.load(json_file)
    except:
        settings = {}

    if settings.get('name') == None:
        settings['name'] = input('Enter a name for the process/settings: ')
        updateSettings(settings,settingsFile)

    if settings.get('ynab_token') == None:
        settings['ynab_token'] = input('Enter YNAB TOKEN :: https://app.youneedabudget.com/settings/developer \n')
        ynabAPI = YNAB_api(settings['ynab_token'])
        while ynabAPI.credential_check == False:
            print('Wrong TOKEN!!')
            settings['ynab_token'] = input('Enter YNAB TOKEN :: https://app.youneedabudget.com/settings/developer \n')
            ynabAPI = YNAB_api(settings['ynab_token'])
        print('Authorized TOKEN!\n')
        updateSettings(settings,settingsFile)

    if settings.get('ynab_budget') == None:
        print('YNAB Budget not selected.')
        settings['ynab_budget'] = ynabAPI.choose_budget()
        updateSettings(settings,settingsFile)

    if settings.get('sbanken_customerid') == None:
        credential_check = False
        while credential_check == False:
            settings['sbanken_customerid'] = input('Enter SBANKEN CUSTOMERID :: https://github.com/Sbanken/api-examples#faq \n')

            settings['sbanken_clientid'] = input('Enter SBANKEN CLIENTID :: https://github.com/Sbanken/api-examples#availability \n')

            settings['sbanken_secret'] = input('Enter SBANKEN SECRET :: https://github.com/Sbanken/api-examples#availability \n')

            sbankAPI = Sbanken_api(settings['sbanken_customerid'], settings['sbanken_clientid'], settings['sbanken_secret'])
            credential_check = sbankAPI.credential_checkResult
        print('SBanken Authorized!\n')
        updateSettings(settings,settingsFile)

    if settings['ynab_budget'].get('accounts') == None or len(settings['ynab_budget']['accounts']) == 0:
        print('No linked account found!')
        settings['ynab_budget']['accounts'] = []
        settings = link_accounts(settings)
        updateSettings(settings,settingsFile)

    return settings

def link_accounts(settings):
    sbankAPI = Sbanken_api(settings['sbanken_customerid'], settings['sbanken_clientid'], settings['sbanken_secret'])
    print('Choose sbank account to link.')
    sbank_accounts = sbankAPI.get_accounts()
    for i in range(len(sbank_accounts)):
        print(str(i)+': '+ sbank_accounts[i]['name'] + ' -- ' + sbank_accounts[i]['accountNumber'])
    sbank_account = int(input('Choose a number: '))
    while sbank_account not in range(len(sbank_accounts)):
        sbank_account = int(input('Choose a number listed: '))

    print('Choose YNAB account to link.')
    r = requests.get(url="https://api.youneedabudget.com/v1/budgets/"+settings['ynab_budget']['id']+"/accounts", headers={'Authorization': 'Bearer '+settings['ynab_token']})
    ynab_accounts = r.json()['data']['accounts']
    for i in range(len(ynab_accounts)):
        print(str(i)+': '+ ynab_accounts[i]['name'] + ' -- ' + ynab_accounts[i]['type'])
    ynab_account = int(input('Choose a number: '))
    while ynab_account not in range(len(ynab_accounts)):
        ynab_account = int(input('Choose a number listed: '))

    settings['ynab_budget']['accounts'].append({'id': ynab_accounts[ynab_account]['id'], 'name': ynab_accounts[ynab_account]['name'], 'account_linked': sbank_accounts[sbank_account]['accountId'], 'account_name': sbank_accounts[sbank_account]['name'], 'to': 'SBanken'})
    return settings

def updateSettings(settings, settingsFile):
    print('Updating "'+settingsFile+'" with current settings')
    with open(settingsFile, 'w') as json_file:
        json.dump(settings, json_file, indent=4)

def processEditor(process):
    inEditor = True
    while inEditor:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('Current wait time: '+str(int(process.waitTime/60))+'minutes.')
        print('Looking '+str(process.daysBack)+' days back to check for transactions.')
        print('Used '+str(process.ynabAPI.requestCounter)+' YNAB requests.')
        print('---------------')
        print('d | Change how many (d)ays back it look for transactions.')
        print('t | Change wait (t)ime between transaction sync.')
        print('l | Link accounts.')
        print('s | Save settings.')
        print('k | Kill process.')
        print('b | Back to menu.')
        user_input = input('Choose an option: ')
        if user_input == 'b': # Back
            inEditor = False
        elif user_input == 'k': # kill
            stopThread(process)
            inEditor = False
        elif user_input == 'd': # daysBack
            process.daysBack = int(input('How many days back? : '))
        elif user_input == 't': # waitTime
            process.waitTime = int(input('How many minutes between syncs? : '))*60
        elif user_input == 'l': # waitTime
            process.settings = link_accounts(process.settings)
        elif user_input == 's': # save
            settingsFile = input('Filename for settingsfile. (Created if not found): ')
            settings = process.settings
            settings['wait_time'] = process.waitTime
            settings['days_back'] = process.daysBack
            updateSettings(settings, settingsFile)


thread_objects = []
threads = {}
def newThread(settings):
    process_Obj = Sync_process(settings)
    thread_objects.append(process_Obj)
    process_thread = threading.Thread(target=process_Obj.main_loop)
    threads[settings['name']] = process_thread
    process_thread.start()
def stopThread(process_Obj):
    process_Obj.run = False
    del threads[process_Obj.settings['name']]
    thread_objects.remove(process_Obj)

if len(sys.argv) == 2 :
    settingsFile = sys.argv[1]
else:
    settingsFile = None

if settingsFile != None:
    settings = create_check_settingsFile(settingsFile)
    newThread(settings)
    #process_Obj=Sync_process(settings)
    #process_Obj.main_loop()

running = True
while running:
    os.system('cls' if os.name == 'nt' else 'clear')
    ynab_requests = 0
    print('Running threads:')
    for i in range(len(thread_objects)):
        print(str(i)+" | "+thread_objects[i].settings['name'])
        ynab_requests += thread_objects[i].ynabAPI.requestCounter
    print('Total YNAB Requests: '+str(ynab_requests))
    print('---------------')

    print('n | New (thread) process with another setting')
    print('q | Quit the Program.')
    user_input = input('Choose an option: ')
    if user_input == 'q': # Quit
        for process in thread_objects:
            process.run = False
        running = False
    elif user_input == 'n': # New process with different settings
        settingsFile = input('Filename for settingsfile. (Created if not found): ')
        settings = create_check_settingsFile(settingsFile)
        newThread(settings)
    # Selecting process
    elif user_input.isdigit() and int(user_input) in range(len(thread_objects)):
        process = thread_objects[int(user_input)]
        processEditor(process)
