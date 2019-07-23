import os
import sys, logging
logging.basicConfig()
logger = logging.getLogger('YNAB_Sync')

cli = False
cron = False
debug = False
settings_files = []

def cli_arguments():
    global cli, cron, debug, settings_files
    skip_one = True
    for i in range(len(sys.argv)):
        if skip_one:
            skip_one = False
            continue
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


def main():
    cli_arguments()
    global cli, cron, debug, settings_files

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if cli:
        from functions import cli
        cli.main(settings_files, cron)
    else:
        import gui
        gui.main(settings_files)


if __name__ == '__main__':
    main()
