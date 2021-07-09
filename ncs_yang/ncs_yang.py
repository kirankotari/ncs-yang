import logging

from utils import Utils
from pathlib import Path
from makefile import MakeFile


class NcsYang(Utils):
    name = 'ncs-yang'
    command = []
    ncs_yang_options = []
    generate_uml = False
    generate_jtox = False
    base_dir = ''
    version = '1.1.1'

    _instance = None
    _ncs_yang_help = None

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
    <YangFile or YangFiles> [--uml | --jtox]
    -h | --help
    -v | --version
'''
        self._ncs_yang_help = output

    @property
    def options(self):
        if len(self.ncs_yang_options):
            return
        self._uml = '--uml'
        self._jtox = '--jtox'
        self._help = ['-h', '--help']
        self._version = ['-v', '--version']
        self.ncs_yang_options = self._help + self._version

    @property
    def get_version(self):
        # need to print
        print('ncs-yang version {}'.format(self.version))
        self._exit

    def generate_uml_diagram(self, id):
        commands = [
            "cp -r {} /tmp/{}".format(self.path.as_posix(), id),
            "pyang -f uml /tmp/{}/{} --uml-no=import,annotation --uml-output-directory=. 1> {}.uml 2> /dev/null".format(id, self.path.name, self.path.stem)
        ]
        for each in commands:
            self._run_bash_command_and_forget(each)

        self.clean_uml()
        self.logger.info("generated uml diagram: {}.uml".format(self.path.stem))

    def generate_jtox_files(self, id):
        commands = [
            "cp -r {} /tmp/{}".format(self.path.as_posix(), id),
            "pyang -f jtox /tmp/{}/{} -o {}.jtox 2> /dev/null".format(id, self.path.name, self.path.stem)
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

        if len(cmd_lst) > 1 and self._uml in cmd_lst:
            self.generate_uml = True

        if len(cmd_lst) > 1 and self._jtox in cmd_lst:
            self.generate_jtox = True

        ncsc_path = self.get_ncsrc_path()
        for each_yang in cmd_lst:
            if each_yang == self._uml or each_yang == self._jtox:
                continue
            if self.is_yang_file(each_yang):
                self.fetch_paths(cmd_lst[0])
                obj = MakeFile()
                yang_paths = obj.read(self.make_path)
                yang_paths = yang_paths.get('YANGPATH', '').split()

                if self.generate_uml:
                    self.workspace(yang_paths, ncsc_path, create=True)
                    self.generate_uml_diagram(self.id)
                    continue
                if self.generate_jtox:
                    self.workspace(yang_paths, ncsc_path, create=True)
                    self.generate_jtox_files(self.id)
                    continue
                
                ncs_yang_command = '{} `ls {}-ann.yang > /dev/null 2>&1 && echo "-a {}-ann.yang"`'.format(ncsc_path, self.p.stem, self.p.stem)
                for each in yang_paths:
                    each = Path("{}/src/{}".format(self.cpkg_path, each)).absolute()
                    ncs_yang_command += ' --yangpath {}'.format(each)
                ncs_yang_command += ' -c -o {}/{}.fxs {}'.format(self.load_dir_path, self.p.stem, each_yang)
                self.logger.info("compiling yang file: {}\n {}".format(each_yang, ncs_yang_command))
                self._run_bash_command_and_forget(ncs_yang_command)

        if self.generate_uml:
            self.workspace(None, None, delete=True)
        self._exit



