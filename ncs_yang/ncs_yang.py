import os
import re
import sys
import logging
import subprocess
import string, random
from pathlib import Path


class Utils:
    name = 'utils'

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


class MakeFile:
    def read(self, fpath):
        data = self.read_data(fpath)
        self.vars = self.get_variables(data)
        return self.vars

    def read_data(self, fpath):
        fp = open(fpath) 
        data = fp.readlines()
        fp.close()
        return data

    def remove_comment(self, data, comment='#'):
        i = data.find(comment)
        if i >= 0:
            data = data[:i]
        return data.strip()

    def get_variables(self, data, add_oper=' '):
        makevar = re.compile(r'^([a-zA-Z0-9_]+)[\s\t]*([\+=]*)(.*?)([\\#]+.*)?$')
        addvar = re.compile(r'^([^=]+)$')
        addvar_flag = False
        vars = {}
        for each in data:
            if addvar_flag is False:
                result = re.search(makevar, each)
                if result is None:
                    continue
                name, oper, value, end = result.groups()
                if oper == '':
                    continue

                if name in vars:
                    vars[name] += add_oper + value.rstrip()   
                else:
                    vars[name] = value.rstrip()
                
                if end is None:
                    continue
                end = self.remove_comment(end)
                if '\\' in end:
                    addvar_flag = True
                continue

            if name is None:
                continue
            result = re.search(addvar, each)
            value, = result.groups()
            value = self.remove_comment(value)
            if value is None:
                continue
            if '\\' not in value:
                addvar_flag = False
            value = self.remove_comment(value, '\\')
            vars[name] += add_oper + value
        return vars


class NcsYang(Utils):
    name = 'ncs-yang'
    command = []
    ncs_yang_options = []
    generate_uml = False
    base_dir = ''
    version = '1.1.1'

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
            # need to print
            print(self._ncs_yang_help)
            self._exit
        output = '''
ncs-yang 
    <filename.yang> [--uml]
    <path-to-filename.yang> [--uml]
    -h | --help
    -v | --version
'''
        self._ncs_yang_help = output

    @property
    def options(self):
        if len(self.ncs_yang_options):
            return
        self._uml = '--uml'
        self._help = ['-h', '--help']
        self._version = ['-v', '--version']
        self.ncs_yang_options = self._help + self._version

    @property
    def get_version(self):
        # need to print
        print('ncs-yang version {}'.format(self.version))
        self._exit

    def id_generator(self, size=10, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def create_workspce(self, id, yang_paths, ncsc_path):
        ncs_yang_path = Path(ncsc_path).parent.parent.as_posix() + "/src/ncs/yang/"
        commands = [
            "mkdir /tmp/{}".format(id),
            "cp -r {} {} /tmp/{}".format(
                ncs_yang_path, 
                " ".join(yang_paths), 
                id)
        ]
        for each in commands:
            self._run_bash_command_and_forget(each)

    def destroy_workspace(self, id):
        self._run_bash_command_and_forget("rm -rf /tmp/{}".format(id))

    def generate_uml_diagram(self, id):
        commands = [
            "cp -r {} /tmp/{}".format(self.path.as_posix(), id),
            "pyang -f uml /tmp/{}/{} --uml-no=import,annotation --uml-output-directory=. 1> {}.uml 2> /dev/null".format(id, self.path.name, self.path.stem)
        ]
        for each in commands:
            self._run_bash_command_and_forget(each)

        self.clean_uml()
        self.logger.info("generated uml diagram: {}.uml".format(self.path.stem))
        
    def clean_uml(self):
        lines = open("{}.uml".format(self.path.stem), "r").readlines()
        for i, line in enumerate(lines):
            if 'startuml' in line:
                start_index = i
            if 'center footer' in line:
                end_index = i
        lines = ['@startuml {}\n'.format(self.path.stem)] + lines[start_index+1:end_index] + ['@enduml', '\n']
        open("{}.uml".format(self.path.stem), "w").writelines(lines)
        

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

    def get_ncsrc_path(self, cmd=['which', 'ncsc']):
        try:
            output = self._run_bash_command_and_collect(cmd)
            if output == '':
                raise FileNotFoundError
        except ValueError as e:
            self.logger.error(e)
            self._exit
        except FileNotFoundError as e:
            self.logger.error('ncsc command not found. please source ncsrc file')
            self._exit
        return output.strip()

    def run_command(self, cmd_lst):
        if cmd_lst[0] in self._version:
            self.get_version
        if cmd_lst[0] in self._help:
            self.help

        id = self.id_generator()
        if len(cmd_lst) > 1 and self._uml in cmd_lst:
            self.generate_uml = True

        for each_yang in cmd_lst:
            if each_yang == self._uml:
                continue
            if self.is_yang_file(each_yang):
                self.fetch_paths(cmd_lst[0])
                ncsc_path = self.get_ncsrc_path()
                obj = MakeFile()
                yang_paths = obj.read(self.make_path)
                yang_paths = yang_paths.get('YANGPATH', '').split()

                if self.generate_uml:
                    self.create_workspce(id, yang_paths, ncsc_path)
                    self.generate_uml_diagram(id)
                    continue
                
                ncs_yang_command = '{} `ls {}-ann.yang > /dev/null 2>&1 && echo "-a {}-ann.yang"`'.format(ncsc_path, self.p.stem, self.p.stem)
                for each in yang_paths:
                    each = Path("{}/src/{}".format(self.cpkg_path, each)).absolute()
                    ncs_yang_command += ' --yangpath {}'.format(each)
                ncs_yang_command += ' -c -o {}/{}.fxs {}'.format(self.load_dir_path, self.p.stem, each_yang)
                self.logger.info("compiling yang file: {}\n {}".format(each_yang, ncs_yang_command))
                self._run_bash_command_and_forget(ncs_yang_command)

        if self.generate_uml:
            self.destroy_workspace(id)
        self._exit

def run():
    obj = NcsYang()
    if len(sys.argv) >= 2:
        if 'yang' not in sys.argv[1] and sys.argv[1] not in obj.ncs_yang_options:
            obj.help
        obj.run_command(sys.argv[1:])
    else:
        obj.help


if __name__ == "__main__":
    run()

