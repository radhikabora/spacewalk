#!/usr/bin/env python
# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# The (.dep) file grammar is as follows:
#
# path : 'path' '=' nslist
#
# nslist :  namespace
#   | nslist \s namespace
#   | nslist ',' namespace
#
# entry : qname '::' deplist
#
# qname : [namespace/]basename[.ext]
#
# deplist : dependency 
#   | deplist \s dependency
#   | deplist ',' dependency
#
# dependency : qname
#

import sys, os, re
from getopt import getopt, GetoptError

#
# CLASSES
#

class Name:
    
    @classmethod
    def qualify(cls, nss, fn):
        names = []
        if cls.qualified(fn):
            for bn in cls.basenames(fn):
                names.append(bn)
            return tuple(names)
        if not isinstance(nss, (tuple,list)):
            nss = (nss,)
        for ns in nss:
            for bn in cls.basenames(fn):
                name = '%s/%s' % (ns, bn)
                names.append(name)
        return tuple(names)
    
    @classmethod
    def basenames(cls, fn):
        names = [fn]
        try:
            basename, ext = fn.rsplit('.', 1)
            names.append(basename)
        except:
            pass
        return names

    @classmethod
    def qualified(cls, name):
        return ( '/' in name )
    
    @classmethod
    def unqualified(cls, name):
        return ( not cls.qualified(name) )
    
    
class DepTab:
    
    class Options(object):
        def __setitem__(self, k, v):
            setattr(self, k, v)
    
    class Entry:
        def __init__(self, tab, info, subject):
            self.tab = tab
            self.info = info
            self.subject = subject
            self.deps = ()
            self.hits = 0
            
        def __iter__(self):
            expanded = self.expanded([])
            return iter(expanded)
        
        def expanded(self, history):
            deps = []
            for keyset in self.deps:
                keyset, expanded = self.tab.expand(keyset, history)
                if len(keyset):
                    deps.append(tuple(keyset))
                deps += expanded
            return deps
            
            
        def __repr__(self):
            s = []
            s.append(self.subject)
            s.append('::')
            s.append(str(self.deps))
            s.append('@')
            s.append(self.info)
            s.append('/%d' % self.hits)
            return ''.join(s)
        
    pattern = re.compile('[,\s]+')
            
    def __init__(self):
        self.content = []
        self.index = {}
        self.options = self.Options()
        self.aliases = None
        
    def read(self, ns, path):
        fp = open(path)
        self.options.path = (ns,)
        for line in self.lines(fp):
            if self.setoption(ns, line[1]):
                continue
            parts = line[1].split('::', 1)
            if len(parts) < 2:
                continue
            info = '%s:%d' % (path, line[0])
            subject = parts[0].strip()
            entry = self.Entry(self, info, subject)
            parts[1] = parts[1].replace('\\', '')
            deps = []
            for dep in self.values(parts[1]):
                dep = dep.strip()
                if not len(dep):
                    continue
                qnames = []
                for qn in Name.qualify(self.options.path, dep):
                    qnames.append(qn)
                deps.append(tuple(qnames))
            entry.deps = tuple(deps)
            self.content.append(entry)
            for key in Name.qualify(ns, subject):
                self.index[key] = entry
        fp.close()
        
    def setoption(self, ns, line):
        parts = line.split('=', 1)
        if len(parts) == 2:
            tag = parts[0].strip()
            if tag == 'path':
                values = []
                for v in self.values(parts[1]):
                    if v == '.':
                        v = ns
                    values.append(v)
                self.options[tag] = values
                return True
        return False
    
    def values(self, line):
        return self.pattern.split(line.strip())
    
    def lines(self, fp):
        ln = 0
        lines = []
        append = False
        for line in fp.readlines():
            ln += 1
            if not len(line):
                continue
            if line[0] == '#':
                continue
            if len(lines) and lines[-1][1].endswith('\\\n'):
                last = lines.pop()[1][:-2]
                joined = ' '.join((last, line))
                lines.append((ln, joined))
            else:
                lines.append((ln, line)) 
        return lines
    
    def find(self, ns, fn):
        result = ()
        for key in Name.qualify(ns, fn):
            entry = self.index.get(key)
            if entry is None:
                continue
            entry.hits += 1
            result = entry
            break
        return result
    
    def expand(self, keyset, history):
        result = ([],[])
        for key in keyset:
            if key in history:
                print 'circular dependency:%s' % history
                continue
            alias = self.aliases.get(key)
            if alias is None:
                result[0].append(key)
                continue
            history.append(key)
            alias.hits += 1
            for deps in alias.expanded(history):
                result[1].append(deps)
        if len(result[1]):
            result = ([], result[1])
        return result
            
    def findaliases(self):
        self.aliases = {}
        for s,e in self.index.items():
            if e.hits == 0:
                self.aliases[s] = e
        return self

class Reader:
    
    EXT = ['sql', 'pks', 'pkb']
    
    def __init__(self):
        self.deptab = DepTab()
        self.deplist = DepList()
        self.overrides = []
        
    def read(self, directories):
        self.opendeptabs(directories)
        self.getfiles(directories)
        self.deptab.findaliases()
        return self
        
    def sort(self):
        sorted = self.deplist.sort()
        return [x[2] for x in sorted]
        

    def opendeptabs(self, directories):
        for d in directories:
            for fn, path in self.files(d, ('deps',)):
                self.deptab.read(d, path)
        return self
        
    def getfiles(self, directories):
        for d in directories:
            for fn, path in self.files(d, self.EXT):
                entry = self.deptab.find(d, fn)
                keys = Name.qualify(d, fn)
                found = self.deplist.find(keys[0])
                if found is None:
                    self.deplist.add(keys, entry, path)
                    continue
                pk = found[2]
                self.overrides.append((path, pk))
        return self
    
    def path(self, d, fn):
        return '%s/%s' % (d, fn)
        
    def fsort(self, a, b):
        try:
            A = a.rsplit('.', 1)
            B = b.rsplit('.', 1)
            IA = self.EXT.index(A[1])
            IB = self.EXT.index(B[1])
            if IA < IB:
                return -1
            if IA > IB:
                return 1
            return cmp(A[0], B[0])
        except:
            return 0

    def files(self, d, extensions):
        files = []
        for n in sorted(os.walk(d)):
            for fn in sorted(n[2], self.fsort):
                parts = fn.rsplit('.', 1)
                if len(parts) != 2:
                    continue
                if parts[1] in extensions:
                    path = self.path(n[0], fn)
                    files.append((fn, path))
        return files


class Writer:
    
    def write(self, sorted, output):
        raise Exception('not-implemented')
    
    def start(self, output):
        if os.path.exists('start.sql'):
            f = open('start.sql')
            content = f.read()
            output.write(content)
            f.close()


class Oracle(Writer):
    
    def write(self, sorted, output):
        ln = 1
        self.start(output)
        for p in sorted:
            entry = '@%s' % p
            print '%d %s' % (ln, entry)
            ln += 1
            output.write('\n')
            output.write(entry)


class Postgres(Writer):

    def write(self, sorted, output):
        ln = 1
        self.start(output)
        for p in sorted:
            entry = '\\i %s' % p
            print '%d %s' % (ln, entry)
            ln += 1
            output.write('\n')
            output.write(entry)


    
class DepList:

    def __init__(self):
        """ """
        self.unsorted = []
        self.index = {}
        self.reset()
        
    def reset(self):
        self.stack = []
        self.pushed = set()
        self.sorted = []
        self.unfound = []
        
    def add(self, keys, deps, *payload):
        item = [keys, deps]
        item += payload
        item = tuple(item)
        self.unsorted.append(item)
        for key in keys:
            self.index[key] = item
        return self
        
    def sort(self):
        self.reset()
        for item in self.unsorted:
            popped = []
            self.push(item)            
            while len(self.stack):
                try:
                    top = self.top()
                    ref = top[1].next()
                    refd = self.find(ref)
                    if refd is None:
                        info = top[0][1].info
                        self.unfound.append((ref, info))
                        continue
                    self.push(refd)
                except StopIteration:
                    popped.append(self.pop())
                    continue
            for p in popped:
                self.sorted.append(p)
        self.unsorted = self.sorted
        return self.sorted
    
    def find(self, key):
        if not isinstance(key, (tuple,list)):
            key = (key,)
        for k in key:
            v = self.index.get(k)
            if v is not None:
                return v
        return None

    def top(self):
        return self.stack[-1]
    
    def push(self, item):
        if item in self.pushed:
            return
        frame = (item, iter(item[1]))
        self.stack.append(frame)
        self.pushed.add(item)
    
    def pop(self):
        try:
            frame = self.stack.pop()
            return frame[0]
        except:
            pass
    
#
# FUNCTIONS
#

def generate(path, reader, writer, output):
    os.chdir(path)
    out = open(output, 'w')
    ds = []
    for fn in ('class', 
               'types', 
               'tables',  
               'procs',
               'packages',
               'views', 
               'triggers',
               'data',):
        if os.path.isdir(fn):
            ds.append(fn)
    reader.read(ds)
    sorted = reader.sort()
    overrides = reader.overrides
    print '\nOVERRIDES (%d):' % len(overrides)
    print '_____________________________________________________'
    for entry in overrides:
        print '"%s" overridden by "%s"' % entry
    unused = \
        [x for x in reader.deptab.content if x.hits == 0]
    print '\nUNUSED RULES (%d):' % len(unused)
    print '_____________________________________________________'
    for entry in unused:
        if entry.hits == 0:
            print '%s @%s' % (entry.subject,entry.info)
    unfound = reader.deplist.unfound
    print '\nUNFOUND (rule) REFERENCES (%d):' % len(unfound)
    print '_____________________________________________________'
    for unf in unfound:
        print '"%s" @%s' % unf
    print '\n\nFILES (%d):' % len(sorted)
    print '_____________________________________________________'
    writer.write(sorted, out)
    out.close() 
    
def usage():
    s = []
    s.append('Usage mkmain: [OPTIONS]')
    s.append(' Options:')
    s.append('  -h, --help')
    s.append('      Show usage information.')
    s.append('  -s, --style')
    s.append('      The output style (oracle|postres ).')
    s.append('  -o, --output')
    s.append('      The output file path.')
    s.append('  -d, --directory')
    s.append('      The working directory to process.')
    print '\n'.join(s)

def main(argv):
    path = '.'
    reader = Reader()
    writer = Oracle()             
    output = 'main.sql'
    flags = 'hd:o:s:'
    keywords = [
        '--help',
        '--directory',
        '--output',
        '--style',
    ]
    try:          
        opts, args = getopt(argv, flags, keywords)
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage()
                sys.exit(0)
            if opt in ('-o', '--output'):
                output = arg
                continue
            if opt in ('-d', '--directory'):
                path = arg
                continue
            if opt in ('-s', '--style'):
                if arg == 'oracle':
                    writer = Oracle()
                    continue
                if arg == 'postgres':
                    writer = Postgres()
                    continue
                raise Exception('style "%s" not valid' % arg)
        generate(path, reader, writer, output)          
    except GetoptError, e:
        print e
        usage()
        sys.exit(2)

if __name__ == '__main__':
    main(sys.argv[1:])
    
