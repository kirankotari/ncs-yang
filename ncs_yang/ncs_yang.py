import getpass
import logging

from pathlib import Path

from .utils import Config, Utils, Encryption
from .makefile import MakeFile


class NcsYang(Utils, Encryption):
    name = 'ncs-yang'
    command = []
    ncs_yang_options = []
    workspace_destroy = False
    generate_uml = False
    generate_jtox = False
    generate_dsdl = False
    pyang_path = None
    base_dir = ''
    version = '1.2.3.1'
 
    _instance = None
    _ncs_yang_help = None

    def __new__(cls, log_level=logging.INFO, log_format=None):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, log_level=logging.INFO, log_format=None, *args, **kwargs):
        Utils.__init__(self, log_level, log_format)
        Encryption.__init__(self, self.logger)
        self.log_format = log_format
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
    --yang-sync <settings.yml>          to collect yang files from remote machine
    --payload <payload.json> 
        <YangFile or YangFiles>         will return payload.xml
    --payload <payload.xml>             will return payload.json
    --payload <payload.yml>             will return payload.json
        <YangFile or YangFiles>         will return payload.xml
    --log [info | debug]
    --path <dependency yang path>
    
    
    # TODO: to generate schema
    --schema <yang> [--json | --xml | --yml] 
    # TODO: to validate we need (*.rng, *.sch, *.dsrl)
    --validate <YangFile> <payload>     to validate given payload
    -h | --help
    -v | --version
'''
        self._ncs_yang_help = output

    @property
    def options(self):
        if len(self.ncs_yang_options):
            return
        self._l = '--log'
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

    def loop_commands(self, commands):
        for each in commands:
            self._run_bash_command_and_forget(each)

    def generate_uml_diagram(self, id=None, dep_path=None):
        commands = []
        outpath = "{}.uml".format(self.path.stem)
        if id is None and dep_path is None:
            self.logger.error("either workspace if or dependency path need to be provided..")
        if dep_path is None:
            dep_path = "/tmp/{}".format(id)
            commands.append("cp -R {} {}".format(self.path.as_posix(), dep_path))
        temp = "{} -f uml {} --path={} --uml-no=import,annotation --uml-output-directory=. 1> {} 2> /dev/null"
        commands.append(
            temp.format(self.pyang_path, self.path.name, dep_path, outpath)
        )
        self.loop_commands(commands)

        self.clean_uml()
        if Path(outpath).exists():
            self.logger.info("generated uml diagram: {}".format(outpath))
        else:
            self.logger.error("failed to generate uml diagram")
        return outpath

    def generate_jtox_files(self, id=None, dep_path=None):
        commands = []
        outpath = "{}.jtox".format(self.path.stem)
        if id is None and dep_path is None:
            self.logger.error("either workspace if or dependency path need to be provided..")
        if dep_path is None:
            dep_path = "/tmp/{}".format(id)
            commands.append("cp -R {} {}".format(self.path.as_posix(), dep_path))
        commands.append(
            "{} -f jtox {} --path={} -o {} 2> /dev/null".format(self.pyang_path, self.path.name, dep_path, outpath)
        )
        self.loop_commands(commands)

        if Path(outpath).exists():
            self.logger.info("generated jtox file: {}".format(outpath))
        else:
            self.logger.error("failed to generate jtox file")
        return outpath

    def generate_dsdl_files(self, id=None, dep_path=None):
        commands = []
        outpath = "{}.dsdl".format(self.path.stem)
        if id is None and dep_path is None:
            self.logger.error("either workspace if or dependency path need to be provided..")
        if dep_path is None:
            dep_path = "/tmp/{}".format(id)
            commands.append("cp -R {} {}".format(self.path.as_posix(), dep_path))
        temp = "{} -f dsdl {} --path={} --dsdl-no-documentation --dsdl-no-dublin-core --dsdl-lax-yang-version -o {}"
        commands.append(
            temp.format(self.pyang_path, self.path.name, dep_path, outpath)
        )
        self.loop_commands(commands)

        if Path(outpath).exists():
            self.logger.info("generated dsdl file: {}".format(outpath))
        else:
            self.logger.error("failed to generate dsdl file")
        return outpath

    def check_pyang_files(self):
        command = "which pyang"
        # TODO: type -a pyang will list python and ncs pyang paths.
        self.pyang_path = str(self._run_bash_command_and_collect(command)).strip()
        if 'pyang' not in self.pyang_path:
            self.logger.error("pyang is not installed, please install pyang command: `pip install pyang`")
            self._exit

        if 'python' not in self.pyang_path.lower() and 'pyenv' not in self.pyang_path.lower():
            self.logger.error("we are getting ncs pyang, but we required python pyang")
            self.logger.error("add python path before ncs path, and source them.")
            self._exit

        paths =[
            "/usr/local/share/yang",
            "/usr/local/share/yang/modules",
            "/usr/local/share/yang/schema",
            "/usr/local/share/yang/xslt",
        ]
        for each in paths:
            if Path(each).exists() == False:
                return False
        return True

    def copy_pyang_files(self):
        if self.pyang_path is None or self.pyang_path == '':
            self.logger.error("""your liunx/unix system doesn't support `which pyang`, install which command: \n
            for CentOS-7 : `yum install which` \n
            for CentOS-8 : `dnf install which` \n
            """)
        ypath = Path(self.pyang_path).parent.parent / "share/yang"
        command = "cp -R {} /usr/local/share/".format(ypath)
        self._run_bash_command_and_forget(command)
        
    def yang_sync(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            self.logger.error("File not found: {}, is the given file valid?".format(file_path))
            self._exit
        args = Config.read_yaml(file_path)

        if not args.get('host'):
            args['host'] = '127.0.0.1'
            self.logger.warning("expecting host: <host>, default host 127.0.0.1 set")
        if not args.get('port'):
            args['port'] = 22
            self.logger.warning("expecting port: <port>, default port 22 set")
        if not args.get('username'):
            args['username'] = 'admin'
            self.logger.warning("expecting username: <username>, default user admin set")
        if not args.get('packages'):
            self.logger.error("expecting packages: <nso-packages-path>")
            self._exit
        if not args.get('ncs_path'):
            self.logger.error("expecting ncs_path: <ncs-path>, in the remote machine type `which ncs`")
            self._exit
        if not args.get('local_path'):
            self.workspace(None, None, create=True)
            args['local_path'] = '/tmp/{}'.format(self.id)

        x = None
        if args.get('ask_password'):
            x = getpass.getpass("Enter remote machine password: ")
        else:
            if not Path("./remote_password.bin").exists():
                self.logger.warning("Couldn't able to find password file in the current directory")
                x = getpass.getpass("Enter remote machine password to continue: ")
            else:
                x = self.data(hostname=args['host'], username=args['username'], decrypt=True)

        if args.get('store_password'):
            self.data(password=x, hostname=args['host'], username=args['username'])
        
        command = "which sshpass"
        result = self._run_bash_command_and_collect(command)
        if "sshpass" not in result:
            self.logger.error("""sshpass is not installed, please install sshpass command: \n
            for CentOS : `yum install sshpass` \n
            for MacOs : `brew install sshpass` \n
            for Ubuntu : `apt-get install sshpass` \n
            """)
            self._exit        

        temp = args['local_path'] + '-temp'
        commands = [
            "mkdir -p {}".format(temp),
            "mkdir -p {}".format(args['local_path']),
            "sshpass -p {} scp -r -P {} {}@{}:{} {}".format(
                x,
                args['port'],
                args['username'], 
                args['host'],
                args['packages'],
                temp
            ),
            "sshpass -p {} scp -r -P {} {}@{}:{} {}".format(
                x,
                args['port'],
                args['username'], 
                args['host'],
                Path(args['ncs_path']).parent.parent / 'src/ncs/yang',
                temp
            ),
            "mv `find {} -name *.yang` {}".format(temp, args['local_path']),
            "rm -rf {}".format(temp)
        ]
        for each in commands:
            self._run_bash_command_and_forget(each)
        return args['local_path'] if args['local_path'] else self.id

    def payload(self, cmd_lst, dep_path):
        # need to identify the right yang module
        # need to translate the yang to Jtox
        # need to use JSON2XML to convert
        """
        json2xml -> payload convertion for json to xml
        which pyang
        type -a pyang
        python3 -c "import os as _; print(_.__file__)"
        find . -name <filename>
        """
        payload_file = Path(cmd_lst[0])
        if not payload_file.exists():
            self.logger.error("couldn't able to find given payload")
            self._exit

        list_of_yangs = []
        for each in cmd_lst[1:]:
            if self.is_yang_file(each):
                list_of_yangs.append(each)
            
        if payload_file.suffix == '.json' and len(list_of_yangs) == 0:
            self.logger.error("couldn't able to convert json payload to xml, required yang file.!")
            self._exit

        def json2xml_payload(payload, list_of_yangs, dep_path):
            list_of_toxs = []
            for each in list_of_yangs:
                self.fetch_paths(each)
                list_of_toxs.append(self.caller(self.generate_jtox_files, dep_path))
            xml_file = "{}/{}.xml".format(payload.parent, payload.stem)
            list_of_toxs = " ".join(list_of_toxs)
            command = "json2xml -t config -o {} {} {}".format(xml_file, list_of_toxs, payload.as_posix())
            self._run_bash_command_and_forget(command)

        if payload_file.suffix == '.json':
            json2xml_payload(payload_file, list_of_yangs, dep_path)

        if payload_file.suffix == '.xml':
            json_file = "{}/{}.json".format(payload_file.parent, payload_file.stem)
            Config.write_json(self.xml2json(payload_file), json_file)

        if payload_file.suffix == '.yml':
            data = Config.read_yaml(payload_file)
            json_file = "{}/{}.json".format(payload_file.parent, payload_file.stem)
            Config.write_json(data, json_file)
            if len(list_of_yangs) > 0:
                json2xml_payload(json_file, list_of_yangs, dep_path)

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

    def get_ncsrc_path(self, cmd='which ncsc'):
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

    def run_ncsc(self, each_yang):
        ncsc_path = self.get_ncsrc_path()
        obj = MakeFile()
        if not Path(self.make_path).exists():
            self.logger.error("couldn't able to find Makefile. Invalid path.")
            self._exit
        yang_paths = obj.read(self.make_path)
        yang_paths = yang_paths.get('YANGPATH', '').split()

        ncs_yang_command = '{} `ls {}-ann.yang > /dev/null 2>&1 && echo "-a {}-ann.yang"`'.format(ncsc_path, self.p.stem, self.p.stem)
        for each in yang_paths:
            each = Path("{}/src/{}".format(self.cpkg_path, each)).absolute()
            ncs_yang_command += ' --yangpath {}'.format(each)
        ncs_yang_command += ' -c -o {}/{}.fxs {}'.format(self.load_dir_path, self.p.stem, each_yang)
        self.logger.info("compiling yang file: {}\n {}".format(each_yang, ncs_yang_command))
        self._run_bash_command_and_forget(ncs_yang_command)

    def caller(self, fun, dep_path=None):
        ncsc_path = self.get_ncsrc_path()
        if dep_path is None:
            obj = MakeFile()
            if not Path(self.make_path).exists():
                self.logger.error("couldn't able to find Makefile. Invalid path.")
                self._exit
            yang_paths = obj.read(self.make_path)
            yang_paths = yang_paths.get('YANGPATH', '').split()

            self.workspace_destroy = True
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

        if not self.check_pyang_files():
            self.copy_pyang_files()

        if len(cmd_lst) > 1 and self._l in cmd_lst:
            try:
                index = self.get_index(cmd_lst, self._l)
                log_type = cmd_lst[index + 1]
                if log_type == 'debug':
                    Utils.__init__(self, log_level=logging.DEBUG, log_format=self.log_format)
            except IndentationError:
                self.logger.error("invalid values provided, check 'ncs-yang --help'.")

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
            try:
                index = self.get_index(cmd_lst, self._yang)
                setting_file = cmd_lst[index + 1]
                self.yang_sync(setting_file)
            except IndentationError:
                self.logger.error("invalid values provided, check 'ncs-yang --help'.")
            return

        if len(cmd_lst) > 1 and self._payload in cmd_lst:
            try:
                index = self.get_index(cmd_lst, self._payload)
                self.payload(cmd_lst[index + 1:], dep_path)
            except IndentationError:
                self.logger.error("invalid values provided, check 'ncs-yang --help'.")
            return

        for each_yang in cmd_lst:
            if each_yang in [self._uml, self._jtox, self._dsdl, self._path]:
                continue
            if self.is_yang_file(each_yang):
                self.logger.info("index: 0 for {}, {}".format(cmd_lst[0], each_yang))
                self.fetch_paths(each_yang)
                
                if self.generate_uml:
                    self.caller(self.generate_uml_diagram, dep_path)
                    continue

                if self.generate_jtox:
                    self.caller(self.generate_jtox_files, dep_path)
                    continue

                if self.generate_dsdl:
                    self.caller(self.generate_dsdl_files, dep_path)
                    continue

                self.run_ncsc(each_yang)

        if self.workspace_destroy and self.logger.level > 10:
            self.workspace(None, None, delete=self.workspace_destroy)

        if self.id:
            self.logger.debug("cleanup the /tmp/{} yourself :)".format(self.id))
        self._exit



