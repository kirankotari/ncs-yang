import logging

from pathlib import Path

from .utils import Utils
from .makefile import MakeFile


class NcsYang(Utils):
    name = 'ncs-yang'
    command = []
    ncs_yang_options = []
    generate_uml = False
    generate_jtox = False
    generate_dsdl = False
    pyang_path = None
    base_dir = ''
    version = '1.2.3'
 
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
    <YangFile or YangFiles> [--uml | --jtox | --dsdl]
    <YangFile or YangFiles> [--uml | --jtox | --dsdl] --path <dependency yang path>
    # WIP: --yang-sync <setting.yml> # we collect and store all the yang files
    # WIP: --payload <payload.json> # we return payload.xml
    # TODO: --payload <payload.xml> # we return payload.json
    # TODO: --payload <payload.yml> # we return payload.json
    # TODO: --schema <yang> [--json | --xml | --yml]
    # TODO: --validate <payload> # we use dsdl and other formats to validate
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
        self._dsdl = '--dsdl'
        self._path = '--path'
        self._yang = '--yang-sync'
        self._payload = '--payload'
        self._help = ['-h', '--help']
        self._version = ['-v', '--version']
        self.ncs_yang_options = self._help + self._version

    @property
    def get_version(self):
        # need to print
        print('ncs-yang version {}'.format(self.version))
        self._exit

    def generate_uml_diagram(self, id=None, dep_path=None):
        commands = []
        if id is None and dep_path is None:
            self.logger.error("either workspace if or dependency path need to be provided..")
        if dep_path is None:
            dep_path = "/tmp/{}".format(id)
            commands.append("cp -r {} {}".format(self.path.as_posix(), dep_path))
        temp = "pyang -f uml {} --path={} --uml-no=import,annotation --uml-output-directory=. 1> {}.uml 2> /dev/null"
        commands.append(
            temp.format(self.path.name, dep_path, self.path.stem)
        )
        for each in commands:
            self._run_bash_command_and_forget(each)

        self.clean_uml()
        self.logger.info("generated uml diagram: {}.uml".format(self.path.stem))

    def generate_jtox_files(self, id=None, dep_path=None):
        commands = []
        if id is None and dep_path is None:
            self.logger.error("either workspace if or dependency path need to be provided..")
        if dep_path is None:
            dep_path = "/tmp/{}".format(id)
            commands.append("cp -r {} {}".format(self.path.as_posix(), dep_path))
        commands.append(
            "pyang -f jtox {} --path={} -o {}.jtox 2> /dev/null".format(self.path.name, dep_path, self.path.stem)
        )

        for each in commands:
            self._run_bash_command_and_forget(each)

        self.logger.info("generated jtox file: {}.jtox".format(self.path.stem))

    def generate_dsdl_files(self, id=None, dep_path=None):
        if not self.check_pyang_files():
            print("I need to copy the path's")
            self.copy_yang_files()
        commands = []
        if id is None and dep_path is None:
            self.logger.error("either workspace if or dependency path need to be provided..")
        if dep_path is None:
            dep_path = "/tmp/{}".format(id)
            commands.append("cp -r {} {}".format(self.path.as_posix(), dep_path))
        temp = "pyang -f dsdl {} --path={} --dsdl-no-documentation --dsdl-no-dublin-core --dsdl-lax-yang-version -o {}.dsdl"
        commands.append(
            temp.format(self.path.name, dep_path, self.path.stem)
        )
        
        for each in commands:
            self._run_bash_command_and_forget(each)

        self.logger.info("generated dsdl file: {}.dsdl".format(self.path.stem))

    def check_pyang_files(self):
        command = "which pyang"
        self.pyang_path = self._run_bash_command_and_collect(command)
        print(self.pyang_path)
        if 'pyang' not in self.pyang_path:
            self.logger.error("pyang is not installed, please install pyang command: `pip install pyang`")
            self._exit

        paths =[
            "ls /usr/local/share/yang",
            "ls /usr/local/share/yang/modules",
            "ls /usr/local/share/yang/schema",
            "ls /usr/local/share/yang/xslt",
        ]
        for each in paths:
            if Path(each).exists() == False:
                return False
        print("I already have yang paths")
        return True

    def copy_yang_files(self):
        if self.pyang_path is None:
            self.logger.error("""your liunx/unix system doesn't support `which pyang`, install which command: \n
            for CentOS-7 : `yum install which` \n
            for CentOS-8 : `dnf install which` \n
            """)
        # TODO: Assuming ..share/yang is installed by pyang..!
        ypath = self.pyang_path.parent.parent / "share/yang"
        command = "cp -r {} /usr/local/share/".format(ypath)
        self._run_bash_command_and_forget(command)
        
    def yang_sync(self):
        # TODO: need to fetch from setting.yml
        # TODO: "which sshpass" if the output empty throw an exception message to install sshpass using following commands.
        remote_path, local_user, local_ip, local_path = None, None, None, None
        command = [
            
            "scp `find {} -name *.yang` {}@{}:{}".format(remote_path, local_user, local_ip, local_path),
            "scp --exec=`find <path> -name <expression>` user@host:<path_where_to_copy>"
        ]
        pass

    def payload(self, id=None, dep_path=None):

        # need to translate the yang to Jtox
        # need to use JSON2XML to convert
        """
        json2xml -> payload convertion for json to xml
        which pyang
        type -a pyang
        python3 -c "import os as _; print(_.__file__)"
        find . -name <filename>
        """
        pass

    def clean_uml(self):
        lines = open("{}.uml".format(self.path.stem), "r").readlines()
        start_index, end_index = 0, -1
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

    def caller(self, fun, dep_path=None, yang_paths=None, ncsc_path=None):
        if dep_path is None:
            self.workspace(yang_paths, ncsc_path, create=True)
            fun(id=self.id)
            return
        fun(dep_path=dep_path)

    def run_command(self, cmd_lst):
        dep_path = None
        if cmd_lst[0] in self._version:
            self.get_version
        if cmd_lst[0] in self._help:
            self.help

        if len(cmd_lst) > 1 and self._path in cmd_lst:
            try:
                index = self.get_index(cmd_lst, self._path)
                dep_path = cmd_lst[index + 1]
            except IndentationError:
                self.logger.error("invalid values provided, check 'ncs-yang --help'.")

        if len(cmd_lst) > 1 and self._uml in cmd_lst:
            self.generate_uml = True

        if len(cmd_lst) > 1 and self._jtox in cmd_lst:
            self.generate_jtox = True
        
        if len(cmd_lst) > 1 and self._dsdl in cmd_lst:
            self.generate_dsdl = True

        if len(cmd_lst) > 1 and self._yang in cmd_lst:
            return

        if len(cmd_lst) > 1 and self._payload in cmd_lst:
            return

        for each_yang in cmd_lst:
            yang_paths = []
            if each_yang in [self._uml, self._jtox, self._dsdl, self._path]:
                continue
            if self.is_yang_file(each_yang):
                self.fetch_paths(cmd_lst[0])
                ncsc_path = self.get_ncsrc_path()
                if dep_path is None:
                    obj = MakeFile()
                    yang_paths = obj.read(self.make_path)
                    yang_paths = yang_paths.get('YANGPATH', '').split()

                if self.generate_uml:
                    self.caller(self.generate_uml_diagram, dep_path, yang_paths, ncsc_path)
                    continue

                if self.generate_jtox:
                    self.caller(self.generate_jtox_files, dep_path, yang_paths, ncsc_path)
                    continue

                if self.generate_dsdl:
                    self.caller(self.generate_dsdl_files, dep_path, yang_paths, ncsc_path)
                    continue

                ncs_yang_command = '{} `ls {}-ann.yang > /dev/null 2>&1 && echo "-a {}-ann.yang"`'.format(ncsc_path, self.p.stem, self.p.stem)
                for each in yang_paths:
                    each = Path("{}/src/{}".format(self.cpkg_path, each)).absolute()
                    ncs_yang_command += ' --yangpath {}'.format(each)
                ncs_yang_command += ' -c -o {}/{}.fxs {}'.format(self.load_dir_path, self.p.stem, each_yang)
                self.logger.info("compiling yang file: {}\n {}".format(each_yang, ncs_yang_command))
                self._run_bash_command_and_forget(ncs_yang_command)

        if self.generate_uml or self.generate_dsdl or self.generate_jtox:
            self.workspace(None, None, delete=True)
        self._exit



