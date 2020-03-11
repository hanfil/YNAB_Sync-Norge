import os
import sys
import argparse
import logging


logging.basicConfig(filename='YNAB_Sync-Norge.log',
                    format='%(asctime)s <%(levelname)s>:%(message)s',
                    filemode='w')
logger = logging.getLogger('YNAB_Sync')
logger.setLevel(logging.INFO)


if getattr(sys, 'frozen', False):
    wd = sys._MEIPASS
    dname = os.path.dirname(sys.executable)
elif __file__:
    wd = os.getcwd()
    dname = os.path.dirname(__file__)
os.chdir(wd)
logger.info("Initializing | Setting working directory: '%s' " % os.getcwd())


""" cli = False
cron = False
debug = False
settings_files = [] """

parser = argparse.ArgumentParser(description="YNAB_Sync-Norge")
parser.add_argument("--settings_files", nargs='+', help="Settings files to load config into program.", default=[])
parser.add_argument("--cli", help="Start the program only in commandline. If not specified defaults to gui.", action='store_true')
parser.add_argument("--cron", help="Usable only with cli. Runs the program only once. Need a settings file.", action='store_true')
parser.add_argument("--debug", help="Prints out debug messages.", action='store_true')
args = parser.parse_args()
print(args)

""" def cli_arguments():
    global cli, cron, debug, settings_files

    skip_one = True
    for i in range(len(sys.argv)):
        if skip_one:
            skip_one = False
        elif sys.argv[i] == '?' or sys.argv[i] == '--help':
            print("[EXAMPLE]\n"
                  "%s [filename] --cli --cron --debug" % __file__ + "\n\n"
                  "[DESCRIPTION]\n"
                  "[filename]    The settings files to start with. Seperate multiple files with spaces.\n"
                  "--cli         Start the program only in commandline. If not specified defaults to gui.\n"
                  "--cron        Usable only with cli. Runs the program only once. Need a settings file.\n"
                  "--debug       Prints out debug messages.\n")
            sys.exit()
        elif sys.argv[i] == '--cli':
            cli = True
        elif sys.argv[i] == '--cron':
            cron = True
        elif sys.argv[i] == '--debug':
            debug = True
        else:
            settings_files.append(sys.argv[i])

 """

def main():
    #cli_arguments()
    #global cli, cron, debug, settings_files

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info(str(logger.getEffectiveLevel))

    if args.cli:
        import YSN_cli
        YSN_cli.CLI(args.settings_files, args.cron)
    else:
        import YSN_gui
        YSN_gui.main(args.settings_files)


if __name__ == '__main__':
    main()
