import sys
import os
import subprocess
import logging

from pathlib import Path


class Utils:
    name = 'utils'

    _instance = None
    def __new__(cls, log_level=logging.INFO, log_format=None):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, log_level=logging.INFO, log_format=None, *args, **kwargs):
        self.__format = log_format
        self.current_path = os.path.abspath('.')
        self.logger = self.__set_logger_level(log_level)

    def __set_logger_level(self, log_level):
        if self.__format is None:
            self.__format = '[ %(levelname)s ] :: [ %(name)s ] :: %(message)s'
        logging.basicConfig(stream=sys.stdout, level=log_level,
                            format=self.__format, datefmt=None)
        logger = logging.getLogger(self.name)
        logger.setLevel(log_level)
        return logger

    def __del__(self):
        self._instance = None

    @property
    def _exit(self):
        sys.exit()

    def _rstrip_digits(self, given_string):
        return given_string.rstrip('1234567890')

    def get_index(self, given_list, element):
        try:
            return given_list.index(element)
        except ValueError:
            return None

    def _is_file(self, fname):
        return os.path.isfile(fname)

    def _is_folder(self, fname):
        return os.path.isdir(fname)

    def _run_bash_commands(self, cmd):
        try:
            subprocess.call(cmd, shell=True)
        except EnvironmentError as e:
            self.logger.error("failed to run command: {}".format(cmd))
            self.logger.error(e)


class MakeFile:
    def read(self, fpath):
        data = self.get_data(fpath)
        vars = self.get_variables(data)

    def get_data(self, fpath):
        fp = open(fpath) 
        data = fp.read()
        data = data.split('\n')
        fp.close()
        return data

    def get_variables(self, data):
        print(data)
        return {}


class NcsYang(Utils):
    name = 'ncs-yang'
    command = []
    ncs_yang_options = []
    base_dir = ''
    version = '1.0.0'

    _instance = None
    _ncs_yang_help = None

    __stdout = subprocess.PIPE
    __stderr = subprocess.PIPE

    def __new__(cls, log_level=logging.INFO, log_format=None):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, log_level=logging.INFO, log_format=None, *args, **kwargs):
        Utils.__init__(self, log_level, log_format)

        # pre-req
        self.help
        self.options

    @property
    def help(self):
        if self._ncs_yang_help:
            print(self._ncs_yang_help)
            self._exit
        output = '''
ncs-yang 
    <filename.yang>
    <path-to-filename.yang>
    -h | --help
    -v | --version
'''
        self._ncs_yang_help = output

    @property
    def options(self):
        if len(self.ncs_yang_options):
            return
        self._help = ['-h', '--help']
        self._version = ['-v', '--version']
        self.ncs_yang_options = self._help + self._version

    @property
    def get_version(self):
        # need to print
        print('ncs-yang version {}'.format(self.version))
        self._exit

    def fetch_paths(self, yang):
        self.path = Path(yang).absolute()
        self.cpkg_path = self.path.parent.parent.parent
        self.load_dir_path = f'{self.cpkg_path}/load-dir'
        self.make_path = f'{self.cpkg_path}/src/Makefile'

    def is_yang_file(self, yang):
        self.p = Path(yang)
        if self.p.suffix != '.yang':
            print(f'skipping file: {yang}')
            return False
        return True

    def run_command(self, cmd_lst):
        print(cmd_lst)
        if cmd_lst[0] in self._version:
            self.get_version
        if cmd_lst[0] in self._help:
            self.help

        self.fetch_paths(cmd_lst[0])
        ncsc_path = 'ncsc' # get path using which ncsc
        obj = MakeFile()
        obj.read(self.make_path)
        # yang_paths = [] # need to read from Makefile
        # for each_yang in cmd_lst:
        #     if self.is_yang_file(each_yang):
        #         ncs_yang_command = f'{ncsc_path} `ls {self.p.stem}-ann.yang > /dev/null 2>&1 && echo "-a {self.p.stem}-ann.yang"`'
        #         for each in yang_paths:
        #             ncs_yang_command += f' --yangpath {each}'
        #         ncs_yang_command += f' -c -o {self.load_dir_path}/{self.p.stem}.fxs {each_yang}'
        #     print(ncs_yang_command)
        # run command
        self._exit
        # if cmd_lst[0] in self._netsim_wrapper_commands:
        #     self.__run_netsim_wrapper__command(['--dir', netsim_dir] + cmd_lst)
        # else:
        #     self.run_ncs_netsim__command(['--dir', netsim_dir] + cmd_lst)
        #     self._exit

def run():
    obj = NcsYang()
    if len(sys.argv) >= 2:
        # if sys.argv[1] not in obj.ncs_yang_options:
        #     obj.help
        obj.run_command(sys.argv[1:])
    else:
        obj.help


if __name__ == "__main__":
    run()

