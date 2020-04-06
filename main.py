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

parser = argparse.ArgumentParser(description="YNAB_Sync-Norge")
parser.add_argument("--settings_files", nargs='+', help="Settings files to load config into program.", default=[])
parser.add_argument("--cli", help="Start the program only in commandline. If not specified defaults to gui.", action='store_true')
parser.add_argument("--cron", help="Usable only with cli. Runs the program only once. Need a settings file.", action='store_true')
parser.add_argument("--debug", help="Prints out debug messages.", action='store_true')
args = parser.parse_args()
logger.debug("initializing | Acquired these input arguments: %s" % args)


def main():
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
