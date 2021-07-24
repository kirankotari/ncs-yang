import os
import sys
import yaml
import json
import errno
import random
import string
import logging
import subprocess
import xml.etree.cElementTree as ET
from collections import OrderedDict
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP

from configparser import ConfigParser, DuplicateSectionError

try:
    unicode
except NameError:
    unicode = str

def config_unicode(string, encoding = "utf-8", errors = "replace"):
    """
    Convert 'string' to Unicode or raise an exception.
    """
    if string == None:
        return None

    if type(string) == unicode:
        return string

    try:
        return unicode(string, encoding, errors)
    except UnicodeDecodeError:
        raise UnicodeDecodeError("Conversion to unicode failed: %r" % string)

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

        def set_logger_level(log_level):
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
        def get_id(size=10, chars=string.ascii_uppercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        def create_workspace(yang_paths, ncsc_path):
            commands = [
                "mkdir /tmp/{}".format(self.id),
            ]
            if yang_paths is not None and len(yang_paths):
                commands.append("cp -R {}/* /tmp/{}".format(" ".join(yang_paths), self.id))

            if ncsc_path is not None:
                ncs_yang_path = Path(ncsc_path).parent.parent / "src/ncs/yang/"
                commands.append("cp -R {}/* /tmp/{}".format(ncs_yang_path.as_posix(), self.id))

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

    def is_yang_file(self, yang, stdout=False):
        self.p = Path(yang)
        if self.p.suffix == '.yang':
            return True

        if stdout:
            print('skipping file: {}'.format(yang))
        return False

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
            self.logger.debug("command '{}' running on shell".format(cmd))
            subprocess.call(cmd, shell=True)
        except EnvironmentError as e:
            self.logger.error("failed to run command: {}".format(cmd))
            self.logger.error(e)

    def _run_bash_command_and_collect(self, command, throw_err=True):
        out, err = None, None
        self.logger.debug("command '{}' running on shell".format(command))
        try:
            p = subprocess.run(command, shell=True, check=True, stdout=self.__stdout, stderr=self.__stderr, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            if throw_err:
                self.logger.error(e)
            return err

        out, err = p.stdout, p.stderr
        if err == '' or 'env.sh' in err:
            return out

    def xml2json(self, xml_path):
        def strip_tag(tag):
            split_array = tag.split('}')
            if len(split_array) > 1:
                tag = split_array[1]
                ns = split_array[0].split('/')[-1]
                return "{}:{}".format(ns, tag)
            return tag

        def elem_to_internal(elem, strip_ns=1, strip=1):
            """Convert an Element into an internal dictionary (not JSON!)."""
            d = OrderedDict()
            elem_tag = elem.tag
            if strip_ns:
                elem_tag = strip_tag(elem.tag)
            for key, value in list(elem.attrib.items()):
                d['@' + key] = value

            # loop over subelements to merge them
            for subelem in elem:
                v = elem_to_internal(subelem, strip_ns=strip_ns, strip=strip)

                tag = subelem.tag
                if strip_ns:
                    tag = strip_tag(subelem.tag)

                value = v[tag]

                try:
                    # add to existing list for this tag
                    d[tag].append(value)
                except AttributeError:
                    # turn existing entry into a list
                    d[tag] = [d[tag], value]
                except KeyError:
                    # add a new non-list entry
                    d[tag] = value
            text = elem.text
            tail = elem.tail
            if strip:
                # ignore leading and trailing whitespace
                if text:
                    text = text.strip()
                if tail:
                    tail = tail.strip()

            if tail:
                d['#tail'] = tail

            if d:
                # use #text element if other attributes exist
                if text:
                    d["#text"] = text
            else:
                # text is the value if no attributes
                d = text or None
            return {elem_tag: d}

        elem = ET.parse(xml_path.as_posix())
        if hasattr(elem, 'getroot'):
            elem = elem.getroot()

        return elem_to_internal(elem)

class Config:
    __config = {}

    @classmethod
    def read(cls, file):
        data = None
        with open(file,"rb") as f:
            data = f.read().strip()
        return data

    @classmethod
    def write(cls, file, data):
        with open(file,"wb") as f:
            f.write(data)
        return True

    @classmethod
    def os_get_path(self, default, envvar):
        path = os.path.expanduser(default)
        if envvar in os.environ and Config.isfile(os.environ[envvar]):
            path = config_unicode(os.environ[envvar])
        return path

    @classmethod
    def read_yaml(cls, fpath):
        data = None
        fpath = fpath if type(fpath) == str else fpath.as_posix()
        with open(fpath, 'r') as stream:
            data = yaml.safe_load(stream)
        return data

    @classmethod
    def write_json(cls, data, fpath):
        fpath = fpath if type(fpath) == str else fpath.as_posix()
        with open(fpath, 'w') as f:
            json.dump(data, f)

class Encryption:
    def __init__(self, logger):
        self.logger = logger

    @classmethod
    def keys(cls, get_private=False, override=False):
        kpaths = {
            "public": [
                Path('~/.ssh/rsa_public.pem').expanduser().as_posix(),
                'RSA_PUBLIC'
            ],
            "private": [
                Path('~/.ssh/rsa_private.pem').expanduser().as_posix(),
                'RSA_PRIVATE'
            ]
        }
        def get_keys(path, get_private):    
            data = [0, 1]
            if get_private:
                data [1] = Config.read(path[1])
            data[0] = Config.read(path[0])
            return data

        def set_keys(pub_path, pri_path):
            try:
                key_pair = RSA.generate(2048)
                if Config.write(pub_path, key_pair.publickey().exportKey('PEM')):
                    Config.write(pri_path, key_pair.exportKey())
                return True

            except IOError as e:
                msg = "%d accessing key file" % (e.errno)
                raise IOError(msg)

        pub_path = Config.os_get_path(*kpaths['public'])
        pri_path = Config.os_get_path(*kpaths['private'])
        if not Path(pub_path).expanduser().is_file() or override == True:
            set_keys(pub_path, pri_path)

        return get_keys(path=[pub_path, pri_path], get_private=get_private)

    def data(self, password=None, hostname=None, username=None, decrypt=False):
        if password is None and hostname is None and username is None and decrypt is False:
            self.logger.error("invalid data encryption method inputs")
            return

        keys = ["{}_{}.bin".format(hostname, username), (0, 0, 0, 0)]
        def enc(data, keys):
            if isinstance(data, str):
                data = data.encode('utf-8')
            public = self.keys()[0]
            recipient_key = RSA.import_key(public)
            session_key = get_random_bytes(16)
            cipher_rsa = PKCS1_OAEP.new(recipient_key)
            enc_session_key = cipher_rsa.encrypt(session_key)
            cipher_aes = AES.new(session_key, AES.MODE_EAX)
            ciphertext, tag = cipher_aes.encrypt_and_digest(data)
            keys[1] = (enc_session_key, cipher_aes.nonce, tag, ciphertext)
            Config.writelines(*keys)

        def decrypt(keys):
            file_in = open(keys[0], "rb")
            private = self.keys(private=True)[1]
            private_key = RSA.import_key(private)
            enc_session_key, nonce, tag, ciphertext = [ file_in.read(x) for x in (private_key.size_in_bytes(), 16, 16, -1) ]
            cipher_rsa = PKCS1_OAEP.new(private_key)
            session_key = cipher_rsa.decrypt(enc_session_key)
            cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
            data = cipher_aes.decrypt_and_verify(ciphertext, tag)
            return data.decode("utf-8")

        if password:
            enc(password, keys)

        if decrypt:
            return decrypt(keys)        

