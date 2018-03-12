import sys


class Logger:
    """
    Handles output printing.
    """

    separator = 45 * '='
    messages = {
        'separator': separator,
        'header': "{} \nWindsOf - NetCDF lidar data converters - v0.1 \n{}".format(separator, separator),
        'bad_config_path': 'No configuration file ({}) found.',
        'inp_path_missing': 'Missing input path config. Use -D to quickly set it.',
        'inp_format_missing': 'Missing input format config. Use -I to quickly set it.',
        'out_format_missing': 'Missing output format config. Use -O to quickly set it.',
        'bad_inp_format': 'Failed to load reader "{}". Native error: {}',
        'bad_out_format': 'Failed to load writer "{}". Native error: {}',
        'input_format_detected': 'Input format detected: {}.',
        'output_format_detected': 'Output format detected: {}.',
        'searching_in_path': 'Looking for input files in {}',
        'found': 'Found {}.',
        'started_r_files': 'Processing {} ...',
        'grouping': 'Grouping files...',
        'writing_file': 'Writing to {} {}.',
        'exit_msg': 'Failed.',
        'files_not_found': 'No valid files were found.',
        'loading_config': 'Loading configurations from {} .',
        'bad_config_file': 'Failed to load config file. ',
        'bad_config_formatting': 'Failed loading; {}',
        'missing_reader_param': 'The config {}, required by the "{}" reader is not set. ' +
                                'Set it under in the .yaml files.',
        'done': 'Done.',
        'about': ''
                 + '   _ _     _                 \n'
                 + '|    | (_)   | |                \n'
                 + '|    | |_  __| | __ _  ___ ___  \n'
                 + '|    | | |/ _` |/ _` |/ __/ _ \ \n'
                 + '|    | | | (_| | (_| | (_| (_) |\n'
                 + '|    |_|_|\__,_|\__,_|\___\___/  v0.0.1\n'
    }
    verbose = False
    _debug = False

    @staticmethod
    def set_args(args):
        """
        Used to set Logger arguments
        :param args: should contain 'verbose', 'debug' attributes
        :return:
        """
        Logger.verbose = args.verbose
        Logger._debug = args.debug

    @staticmethod
    def __print_std_output(prefix, msg_name, *args):
        """
        Prints to standard output.
        :param prefix: message prefix e.g [Error], [Warning]
        :param msg_name: message key
        :param args: arguments to format the message with
        :return: void
        """
        formatted_msg = args[0] if msg_name is None else Logger.messages[msg_name].format(*args)
        if prefix is None:
            print(formatted_msg)
        else:
            print(prefix, formatted_msg)

    @staticmethod
    def header():
        """
        Prints the converter header.
        :return: void
        """
        Logger.__print_std_output(None, 'header')

    @staticmethod
    def log(msg_name, *args):
        """
        Prints a message
        :param msg_name: message name
        :param args: message arguments
        :return:
        """
        Logger.__print_std_output('| ', msg_name, *args)

    @staticmethod
    def info(msg_name, *args):
        """
        Prints a message if verbose mode is set.
        :param msg_name: message name
        :param args: message arguments
        :return:
        """
        if Logger.verbose:
            Logger.__print_std_output('[Info] ', msg_name, *args)

    @staticmethod
    def debug(msg_name, *args):
        """
        Prints a message if debug mode is set.
        :param msg_name: message name
        :param args: message arguments
        :return:
        """
        if Logger._debug:
            Logger.__print_std_output('[Debug] \n', msg_name, *args)

    @staticmethod
    def warn(msg_name, *args):
        """
        Prints a warning.
        :param msg_name: message name
        :param args: message arguments
        :return:
        """
        Logger.__print_std_output('[Warn] ', msg_name, *args)

    @staticmethod
    def error(msg_name, *args):
        """
        Prints an error message and ends the program.
        :param msg_name: message name
        :param args: message arguments
        :return:
        """
        Logger.__print_std_output('[Error] ', msg_name, *args)
        sys.exit()
