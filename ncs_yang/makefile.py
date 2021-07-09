import re


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

