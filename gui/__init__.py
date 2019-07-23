import os, sys, time, json
from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QApplication, QWidget, QPushButton, QAction, QLabel, QTabWidget, QVBoxLayout, QStackedWidget, QFileDialog

from functions import sbanken
from functions import ynab
from functions import sync


# Subclass QMainWindow to customise your application's main window
class App(QMainWindow):

    def __init__(self, settings_files=[]):
        super().__init__()
        self.settings_files = settings_files
        self.settings_json = []

        self.log_list = []
        self.thread_objects = []
        self.threads = {}
        self.initUI()
        self.startupProcess()

    def initUI(self):
        uic.loadUi('./gui/content/mainwindow.ui', self)

        self.settingsNew_import.clicked.connect(self.import_settingsfile)
        self.settings_ynab_token.returnPressed.connect(self.get_ynabbudgets)
        self.settingsNew_getBudgets.clicked.connect(self.get_ynabbudgets)
        self.settingsNew_getAccounts.clicked.connect(self.get_accounts)
        self.settings_ynabAccounts.itemClicked.connect(self.enable_linkAccounts_btn)
        self.settings_sbankAccounts.itemClicked.connect(self.enable_linkAccounts_btn)
        self.settingsNew_linkAccounts.clicked.connect(self.add_linkedAccounts)
        self.settingsNew_load.clicked.connect(self.load_settings)

        self.tabWidget.setCurrentIndex(1)
        self.show()

    def showProcessWidgets(self, process):
        # Check if widget already exist
        if self.info_stack.count() == 0:
            process_pane = uic.loadUi('gui/content/ProcessPane.ui')
        else:
            for i in range(self.info_stack.count()):
                if self.info_stack.tabText(i) == process.settings['name']:
                    process_pane = self.info_stack.widget(i)
                    break
                else:
                    process_pane = uic.loadUi('gui/content/ProcessPane.ui')
        # Update widget
        process_pane.name.setText(process.settings['name'])
        if not process.ynabAPI.accounts:
            process.ynabAPI.list_accounts()
        process_pane.tabWidget.clear()
        accounts = process.settings['ynab_budget']['accounts']
        for account in accounts:
            info_pane = uic.loadUi('gui/content/InfoPane.ui')
            info_pane.ynabAccount_name.setText(account['name'])
            info_pane.sbankAccount_name.setText(account['account_name'])
            # Fetching account info from process
            for acc_info in process.ynabAPI.accounts:
                if acc_info['id'] == account['id']:
                    account_info = acc_info
            info_pane.amount_sum.setText(str(account_info['balance'] / 1000))
            process_pane.tabWidget.addTab(info_pane, account['name'])
        self.info_stack.addTab(process_pane, process.settings['name'])
        self.tabWidget.setCurrentIndex(0)

    def showSettingsWidgets(self, process):
        for i in range(self.settings_stack.count()):
            if self.settings_stack.tabText(i) == process.settings['name']:
                settings_pane = self.settings_stack.widget(i)
                break
            else:
                settings_pane = uic.loadUi('gui/content/SettingsPane.ui')
        settings_pane.settings_name.setText(process.settings['name'])
        settings_pane.settings_sbanken_customerid.setText(process.settings['sbanken_customerid'])
        settings_pane.settings_sbanken_clientid.setText(process.settings['sbanken_clientid'])
        settings_pane.settings_sbanken_secret.setText(process.settings['sbanken_secret'])
        settings_pane.settings_ynab_token.setText(process.settings['ynab_token'])
        settings_pane.settings_ynab_budget_id.setText(process.settings['ynab_budget']['id'])
        settings_pane.settings_ynab_budget_name.setText(process.settings['ynab_budget']['name'])
        settings_pane.settings_ynab_budget_startdate.setDate(QDate.fromString(process.settings['ynab_budget']['startdate'], 'yyyy-MM-dd'))
        if process.settings.get('days_back'):
            settings_pane.settings_days_back.setValue(int(process.settings['days_back']))
        if process.settings.get('wait_time'):
            settings_pane.settings_waitTime.setValue(int(process.settings['wait_time'])/60)
        settings_pane.settings_accountlink.clear()
        if not process.ynabAPI.accounts:
            process.ynabAPI.list_accounts()
        accounts = process.settings['ynab_budget']['accounts']
        for account in accounts:
            linkedAccount_tab = uic.loadUi('gui/content/linkedAccount_tab.ui')
            linkedAccount_tab.id.setText(account['id'])
            linkedAccount_tab.name.setText(account['name'])
            linkedAccount_tab.account_linked.setText(account['account_linked'])
            linkedAccount_tab.account_name.setText(account['account_name'])
            linkedAccount_tab.to.setText(account['to'])
            linkedAccount_tab.remove.hide()
            settings_pane.settings_accountlink.addTab(linkedAccount_tab, account['name'])
        settings_pane.status_icon.setPixmap(QPixmap("gui/icons/green_dot.png"))
        settings_pane.status.setText('Running')
        settings_pane.process_stop.clicked.connect(lambda: self.stopThread(process.settings['name']))
        settings_pane.process_start.clicked.connect(lambda: self.newThread(process.settings))
        settings_pane.process_update.clicked.connect(lambda: self.newThread(self.settings_pane2settings_json(settings_pane)))
        settings_pane.settings_export.clicked.connect(lambda: self.export_settings(settings_pane))
        self.settings_stack.insertTab(0, settings_pane, process.settings['name'])
        self.settings_stack.setCurrentIndex(0)

    def closeEvent(self, event):
        for process in self.thread_objects:
            process.run = False
        # Waiting for the threads to shutdown
        for process in self.thread_objects:
            while process.running:
                time.sleep(0.1)

    def update_statusBar(self, data):
        self.log_list.addItem(data)
        self.statusbar.showMessage(data)

    def update_timer(self, data):
        process_name, timer, waitTime = data
        for i in range(self.info_stack.count()):
            if self.info_stack.tabText(i) == process_name:
                process_pane = self.info_stack.widget(i)
        if waitTime != timer:
            minutes = int(waitTime / 60) - int(timer / 60) - 1
            seconds = 59 - (timer % 60)
            try:
                process_pane.sleepTime.setText('Sleep Time: %s minutes, %s seconds' % (minutes, seconds))
            except: pass

    def startupProcess(self):
        for settingsFile in self.settings_files:
            with open(settingsFile) as json_file:
                settings = json.load(json_file)
            self.settings_json.append(settings)
            self.newThread(settings)

    def newThread(self, settings):
        # Update already running process
        for process_Obj in self.thread_objects:
            if process_Obj.settings['name'] == settings['name']:
                process_Obj.settings = settings
                self.tabWidget.setCurrentIndex(0)
                for i in range(self.info_stack.count()):
                    if self.info_stack.tabText(i) == settings['name']:
                        self.info_stack.setCurrentIndex(i)
                return
        # Create new process
        process_Obj = sync.Process(settings)
        process_Obj.running.connect(self.showProcessWidgets)
        process_Obj.running.connect(self.showSettingsWidgets)
        process_Obj.message.connect(self.update_statusBar)
        process_Obj.timerUpdate.connect(self.update_timer)
        self.thread_objects.append(process_Obj)
        process_Obj.start()
    def stopThread(self, process_name):
        for process_Obj in self.thread_objects:
            if process_Obj.settings['name'] == process_name:
                process_Obj.run = False
                self.thread_objects.remove(process_Obj)
        for i in range(self.info_stack.count()):
            if self.info_stack.tabText(i) == process_name:
                self.info_stack.removeTab(i)
        for i in range(self.settings_stack.count()):
            if self.settings_stack.tabText(i) == process_name:
                settings_pane = self.settings_stack.widget(i)
                settings_pane.status_icon.setPixmap(QPixmap("gui/icons/red_dot.png"))
                settings_pane.status.setText('not Running')

    def load_settings(self, *argv):
        settings = self.settings_pane2settings_json(self)
        settings_match = False
        for current_settings in self.settings_json:
            if current_settings['sbanken_clientid'] == settings['sbanken_clientid']:
                settings_match = True
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText('Lignende instillinger fins allerede!\n SBank clientId: %s' % settings['sbanken_clientid'])
                msg.exec_()
        if not settings_match:
            self.settings_json.append(settings)
            self.newThread(settings)

    def import_settingsfile(self, *argv):
        # Resetting values
        self.settings_days_back.setValue(4)
        self.settings_waitTime.setValue(15 / 60)
        self.settings_sbanken_customerid.setText('')
        self.settings_sbanken_secret.setText('')
        self.settings_sbanken_clientid.setText('')
        self.settings_ynab_token.setText('')
        for i in range(self.settings_accountlink.count() - 1):
            self.settings_accountlink.removeTab(0)
        # Loading settings from file
        fname = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd(), "json files (*.YNAB.json *.json)")
        settingsFile = fname[0]
        if settingsFile:
            with open(settingsFile) as json_file:
                settings = json.load(json_file)
            self.settings_name.setText(settings['name'])
            self.settings_sbanken_customerid.setText(settings['sbanken_customerid'])
            self.settings_sbanken_clientid.setText(settings['sbanken_clientid'])
            self.settings_sbanken_secret.setText(settings['sbanken_secret'])
            self.settings_ynab_token.setText(settings['ynab_token'])
            self.settings_ynab_budget_id.addItem(settings['ynab_budget']['id'])
            self.settings_ynab_budget_name.setText(settings['ynab_budget']['name'])
            self.settings_ynab_budget_startdate.setDate(QDate.fromString(settings['ynab_budget']['startdate'], 'yyyy-MM-dd'))
            if settings.get('days_back'):
                self.settings_days_back.setValue(int(settings['days_back']))
            if settings.get('wait_time'):
                self.settings_waitTime.setValue(int(settings['wait_time'])/60)
            self.add_linkedAccounts(linked_accounts=settings['ynab_budget']['accounts'])

    def export_settings(self, settings_pane):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText('Ikke del filen med andre! \nFilen får innhold av sensitiv opplysninger og rettigheter.')
        msg.exec_()
        fname = QFileDialog.getSaveFileName(self, 'Save file', os.getcwd(), "json files (*.YNAB.json *.json)")
        settingsFile = fname[0]
        if settingsFile:
            settings = self.settings_pane2settings_json(settings_pane)
            with open(settingsFile, 'w') as json_file:
                json.dump(settings, json_file, indent=4)

    def get_ynabbudgets(self, *argv):
        self.settings_ynab_budget_id.clear()
        ynab_token = self.settings_ynab_token.text()
        if ynab_token not in ['', '[skriv inn YNAB token]']:
            ynabAPI = ynab.API(ynab_token)
            if ynabAPI.credential_checkResult:
                self.ynab_budgets = ynabAPI.get_budget()
                for budget in self.ynab_budgets:
                    self.settings_ynab_budget_id.addItem(budget['id'])
                    self.settings_ynab_budget_id.currentIndexChanged.connect(lambda index: self.settings_ynab_budget_name.setText(self.ynab_budgets[index]['name']))
                    self.settings_ynab_budget_id.currentIndexChanged.connect(lambda index: self.settings_ynab_budget_startdate.setDate(QDate.fromString(self.ynab_budgets[index]['first_month'], 'yyyy-MM-dd')))
                self.settings_ynab_budget_name.setText(self.ynab_budgets[0]['name'])
                self.settings_ynab_budget_startdate.setDate(QDate.fromString(self.ynab_budgets[0]['first_month'], 'yyyy-MM-dd'))
            else:
                self.settings_ynab_token.setText(str(ynabAPI.status_text))
        else:
            self.settings_ynab_token.setText('[skriv inn YNAB token]')
            # Refreshing QLineEdit settingsNew_ynab_token
        self.settings_new.hide()
        self.settings_new.show()

    def get_accounts(self, *argv):
        ynab_token = self.settings_ynab_token.text()
        customerid = self.settings_sbanken_customerid.text()
        clientid = self.settings_sbanken_clientid.text()
        secret = self.settings_sbanken_secret.text()
        if ynab_token not in ['', '[skriv inn YNAB token]']:
            ynabAPI = ynab.API(ynab_token)
            if ynabAPI.credential_checkResult:
                if customerid not in ['', '[manglende info]', 'ddmmyyxxxxx']:
                    if clientid not in ['', '[manglende info]', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx']:
                        if secret not in ['', '[manglende info]', 'Wrong Credentials', '********************************************************************']:
                            sbankAPI = sbanken.API(customerid, clientid, secret)
                            if sbankAPI.credential_checkResult: # Every credential check confirmed
                                ynab_budget = self.settings_ynab_budget_id.currentText()
                                if ynab_budget not in ['']:
                                    ynabAPI.choose_budget(ynab_budget)
                                    ynab_accounts = ynabAPI.list_accounts()
                                    for account in ynab_accounts:
                                        self.settings_ynabAccounts.addItem('%s--%s          ::%s::' % (account['name'], account['type'], account['id']))
                                    sbank_accounts = sbankAPI.get_accounts()
                                    for account in sbank_accounts:
                                        self.settings_sbankAccounts.addItem('%s--%s          ::%s::' % (account['name'], account['accountNumber'], account['accountId']))
                                else:
                                    self.settings_ynab_budget_name.setText('Velg YNAB Budget!')
                            else:
                                self.settings_sbanken_secret.setText(sbankAPI.status_text)
                        else:
                            self.settings_sbanken_secret.setText('[manglende info]')
                    else:
                        self.settings_sbanken_clientid.setText('[manglende info]')
                else:
                    self.settings_sbanken_customerid.setText('[manglende info]')
            else:
                self.settings_ynab_token.setText(str(ynabAPI.status_text))
        else:
            self.settings_ynab_token.setText('[skriv inn YNAB token]')

        self.settings_new.hide()
        self.settings_new.show()

    def enable_linkAccounts_btn(self, *argv):
        if len(self.settings_ynabAccounts.selectedItems()) > 0 and len(self.settings_sbankAccounts.selectedItems()) > 0:
            self.settingsNew_linkAccounts.setEnabled(True)

    def add_linkedAccounts(self, *argv, linked_accounts=[]):
        if linked_accounts == []:
            ynab_account = self.settings_ynabAccounts.selectedItems()[0].text()
            sbank_account = self.settings_sbankAccounts.selectedItems()[0].text()
            self.settings_ynabAccounts.takeItem(self.settings_ynabAccounts.currentRow())
            self.settings_sbankAccounts.takeItem(self.settings_sbankAccounts.currentRow())
            linked_accounts.append({'id': ynab_account.split('::')[1],
                                    'name': ynab_account.split('--')[0],
                                    'account_linked': sbank_account.split('::')[1],
                                    'account_name': sbank_account.split('--')[0],
                                    'to': 'SBanken'})
        linked_accounts.reverse()
        for account in linked_accounts:
            linkedAccount_tab = uic.loadUi('gui/content/linkedAccount_tab.ui')
            linkedAccount_tab.id.setText(account['id'])
            linkedAccount_tab.name.setText(account['name'])
            linkedAccount_tab.account_linked.setText(account['account_linked'])
            linkedAccount_tab.account_name.setText(account['account_name'])
            linkedAccount_tab.to.setText(account['to'])
            linkedAccount_tab.remove.clicked.connect(self.remove_linkedAccount)
            self.settings_accountlink.insertTab(0, linkedAccount_tab, account['name'])

        linked_accounts.clear()

    def remove_linkedAccount(self, *argv):
        self.settings_accountlink.removeTab(self.settings_accountlink.currentIndex())

    def settings_pane2settings_json(self, settings_pane):
        settings = {'name': settings_pane.settings_name.text(),
                    'sbanken_customerid': settings_pane.settings_sbanken_customerid.text(),
                    'sbanken_clientid': settings_pane.settings_sbanken_clientid.text(),
                    'sbanken_secret': settings_pane.settings_sbanken_secret.text(),
                    'ynab_token': settings_pane.settings_ynab_token.text(),
                    'ynab_budget': {
                        'name': settings_pane.settings_ynab_budget_name.text(),
                        'startdate': settings_pane.settings_ynab_budget_startdate.date().toString(
                            settings_pane.settings_ynab_budget_startdate.displayFormat()),
                        'accounts': []
                    }}
        try:
            settings['ynab_budget']['id'] = settings_pane.settings_ynab_budget_id.currentText()
        except:
            settings['ynab_budget']['id'] = settings_pane.settings_ynab_budget_id.text()
        settings['days_back'] = int(settings_pane.settings_days_back.text())
        settings['wait_time'] = int(settings_pane.settings_waitTime.text())*60
        for i in range(settings_pane.settings_accountlink.count()):
            if settings_pane.settings_accountlink.tabText(i) == '+':
                continue
            account = settings_pane.settings_accountlink.widget(i)
            settings['ynab_budget']['accounts'].append({
                'id': account.id.text(),
                'name': account.name.text(),
                'account_linked': account.account_linked.text(),
                'account_name': account.account_name.text(),
                'to': account.to.text()
            })
        return settings

def main(settings_files=[]):
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('gui/icons/YNAB-icon.png'))
    app.setApplicationName('YNAB_Sync-Norge')
    ex = App(settings_files)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()