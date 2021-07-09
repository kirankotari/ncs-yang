import os
import sys
import random
import string
import logging
import subprocess

from pathlib import Path


class Utils:
    name = 'utils'
    id = None

    __stdout = subprocess.PIPE
    __stderr = subprocess.PIPE

    _instance = None
    def __new__(cls, log_level=logging.INFO, log_format=None):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, log_level=logging.INFO, log_format=None, *args, **kwargs):
        self.__format = log_format
        self.current_path = os.path.abspath('.')

        def set_logger_level(self, log_level):
            if self.__format is None:
                self.__format = '[ %(levelname)s ] :: [ %(name)s ] :: %(message)s'
            logging.basicConfig(stream=sys.stdout, level=log_level,
                                format=self.__format, datefmt=None)
            logger = logging.getLogger(self.name)
            logger.setLevel(log_level)
            return logger
        
        self.logger = set_logger_level(log_level)

    def __del__(self):
        self._instance = None

    @property
    def _exit(self):
        sys.exit()

    def _rstrip_digits(self, given_string):
        return given_string.rstrip('1234567890')

    def workspace(self, yang_paths, ncsc_path, create=False, delete=False):
        def get_id(self, size=10, chars=string.ascii_uppercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        def create_workspace(yang_paths, ncsc_path):
            ncs_yang_path = Path(ncsc_path).parent.parent.as_posix() + "/src/ncs/yang/"
            commands = [
                "mkdir /tmp/{}".format(self.id),
                "cp -r {} {} /tmp/{}".format(
                    ncs_yang_path, 
                    " ".join(yang_paths), 
                    self.id)
            ]
            for each in commands:
                self._run_bash_command_and_forget(each)

        def destroy_workspace():
            self._run_bash_command_and_forget("rm -rf /tmp/{}".format(self.id))

        if self.id is None:
            self.id = get_id()

        if create == True:
            create_workspace(yang_paths, ncsc_path)
        if delete == True:
            destroy_workspace()

    def fetch_paths(self, yang):
        if os.path.isfile(yang) == False:
            self.logger.error("file not found in the given path.")
            self._exit
        self.path = Path(yang).absolute()
        self.cpkg_path = self.path.parent.parent.parent
        self.load_dir_path = '{}/load-dir'.format(self.cpkg_path)
        self.make_path = '{}/src/Makefile'.format(self.cpkg_path)

    def is_yang_file(self, yang):
        self.p = Path(yang)
        if self.p.suffix != '.yang':
            print('skipping file: {}'.format(yang))
            return False
        return True

    def get_index(self, given_list, element):
        try:
            return given_list.index(element)
        except ValueError:
            return None

    def _is_file(self, fname):
        return os.path.isfile(fname)

    def _is_folder(self, fname):
        return os.path.isdir(fname)

    def _run_bash_command_and_forget(self, cmd):
        try:
            subprocess.call(cmd, shell=True)
        except EnvironmentError as e:
            self.logger.error("failed to run command: {}".format(cmd))
            self.logger.error(e)

    def _run_bash_command_and_collect(self, command, throw_err=True):
        self.logger.debug("command `{}` running on terminal".format(' '.join(command)))
        p = subprocess.Popen(command, stdout=self.__stdout,
                             stderr=self.__stderr)
        out, err = p.communicate()
        out, err = out.decode('utf-8'), err.decode('utf-8')
        if err == '' or 'env.sh' in err:
            self.logger.debug("`{}` ran successfully".format(' '.join(command)))
            return out
        if throw_err:
            self.logger.error("an error occured while running command `{}`".format(' '.join(command)))
            msg = 'message: {}'.format(err)
            if 'command not found' in err or 'Unknown command' in err:
                raise FileNotFoundError("command not found.")
            raise ValueError(msg)

