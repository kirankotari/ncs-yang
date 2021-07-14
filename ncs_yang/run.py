import sys
from ncs_yang.ncs_yang import NcsYang


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