#!/usr/bin/env python3
"""
A Python implementation of the Unix find command.
Usage: python find.py [path...] [expression]
"""

import os
import sys
import re
import stat
import time
import fnmatch
import argparse
import subprocess
from pathlib import Path
from typing import List, Iterator, Callable, Any, Optional, Union

class FindExpression:
    """Base class for find expressions"""
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        raise NotImplementedError

class TrueExpression(FindExpression):
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return True

class FalseExpression(FindExpression):
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return False

class NotExpression(FindExpression):
    def __init__(self, expr: FindExpression):
        self.expr = expr
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return not self.expr.evaluate(path, st)

class AndExpression(FindExpression):
    def __init__(self, left: FindExpression, right: FindExpression):
        self.left = left
        self.right = right
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return self.left.evaluate(path, st) and self.right.evaluate(path, st)

class OrExpression(FindExpression):
    def __init__(self, left: FindExpression, right: FindExpression):
        self.left = left
        self.right = right
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return self.left.evaluate(path, st) or self.right.evaluate(path, st)

class NameExpression(FindExpression):
    def __init__(self, pattern: str, case_sensitive: bool = True):
        self.pattern = pattern
        self.case_sensitive = case_sensitive
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        name = os.path.basename(path)
        if self.case_sensitive:
            return fnmatch.fnmatch(name, self.pattern)
        else:
            return fnmatch.fnmatch(name.lower(), self.pattern.lower())

class PathExpression(FindExpression):
    def __init__(self, pattern: str, case_sensitive: bool = True):
        self.pattern = pattern
        self.case_sensitive = case_sensitive
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        if self.case_sensitive:
            return fnmatch.fnmatch(path, self.pattern)
        else:
            return fnmatch.fnmatch(path.lower(), self.pattern.lower())

class TypeExpression(FindExpression):
    def __init__(self, file_type: str):
        self.file_type = file_type
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        if self.file_type == 'f':
            return stat.S_ISREG(st.st_mode)
        elif self.file_type == 'd':
            return stat.S_ISDIR(st.st_mode)
        elif self.file_type == 'l':
            return stat.S_ISLNK(st.st_mode)
        elif self.file_type == 'b':
            return stat.S_ISBLK(st.st_mode)
        elif self.file_type == 'c':
            return stat.S_ISCHR(st.st_mode)
        elif self.file_type == 'p':
            return stat.S_ISFIFO(st.st_mode)
        elif self.file_type == 's':
            return stat.S_ISSOCK(st.st_mode)
        return False

class SizeExpression(FindExpression):
    def __init__(self, size_spec: str):
        self.size_spec = size_spec
        self._parse_size()
    
    def _parse_size(self):
        size_str = self.size_spec
        
        # Parse prefix (+, -, or exact)
        if size_str.startswith('+'):
            self.comparison = 'gt'
            size_str = size_str[1:]
        elif size_str.startswith('-'):
            self.comparison = 'lt'
            size_str = size_str[1:]
        else:
            self.comparison = 'eq'
        
        # Parse unit suffix
        multiplier = 1
        if size_str.endswith('c'):
            multiplier = 1
            size_str = size_str[:-1]
        elif size_str.endswith('w'):
            multiplier = 2
            size_str = size_str[:-1]
        elif size_str.endswith('b'):
            multiplier = 512
            size_str = size_str[:-1]
        elif size_str.endswith('k'):
            multiplier = 1024
            size_str = size_str[:-1]
        elif size_str.endswith('M'):
            multiplier = 1024 * 1024
            size_str = size_str[:-1]
        elif size_str.endswith('G'):
            multiplier = 1024 * 1024 * 1024
            size_str = size_str[:-1]
        
        try:
            self.target_size = int(size_str) * multiplier
        except ValueError:
            raise ValueError(f"Invalid size specification: {self.size_spec}")
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        file_size = st.st_size
        if self.comparison == 'gt':
            return file_size > self.target_size
        elif self.comparison == 'lt':
            return file_size < self.target_size
        else:
            return file_size == self.target_size

class TimeExpression(FindExpression):
    def __init__(self, time_spec: str, time_type: str):
        self.time_spec = time_spec
        self.time_type = time_type  # 'mtime', 'ctime', 'atime'
        self._parse_time()
    
    def _parse_time(self):
        time_str = self.time_spec
        
        if time_str.startswith('+'):
            self.comparison = 'gt'
            time_str = time_str[1:]
        elif time_str.startswith('-'):
            self.comparison = 'lt'
            time_str = time_str[1:]
        else:
            self.comparison = 'eq'
        
        try:
            self.days = int(time_str)
        except ValueError:
            raise ValueError(f"Invalid time specification: {self.time_spec}")
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        now = time.time()
        
        if self.time_type == 'mtime':
            file_time = st.st_mtime
        elif self.time_type == 'ctime':
            file_time = st.st_ctime
        elif self.time_type == 'atime':
            file_time = st.st_atime
        else:
            return False
        
        age_days = (now - file_time) / (24 * 60 * 60)
        
        if self.comparison == 'gt':
            return age_days > self.days
        elif self.comparison == 'lt':
            return age_days < self.days
        else:
            return int(age_days) == self.days

class EmptyExpression(FindExpression):
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        if stat.S_ISREG(st.st_mode):
            return st.st_size == 0
        elif stat.S_ISDIR(st.st_mode):
            try:
                return len(os.listdir(path)) == 0
            except (OSError, PermissionError):
                return False
        return False

class RegexExpression(FindExpression):
    def __init__(self, pattern: str, case_sensitive: bool = True):
        flags = 0 if case_sensitive else re.IGNORECASE
        self.regex = re.compile(pattern, flags)
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return bool(self.regex.search(path))

class PermExpression(FindExpression):
    def __init__(self, perm_spec: str):
        self.perm_spec = perm_spec
        self._parse_perm()
    
    def _parse_perm(self):
        perm_str = self.perm_spec
        
        if perm_str.startswith('-'):
            self.mode = 'all'
            perm_str = perm_str[1:]
        elif perm_str.startswith('/'):
            self.mode = 'any'
            perm_str = perm_str[1:]
        else:
            self.mode = 'exact'
        
        try:
            self.target_perm = int(perm_str, 8)
        except ValueError:
            raise ValueError(f"Invalid permission specification: {self.perm_spec}")
    
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        file_perm = st.st_mode & 0o777
        
        if self.mode == 'exact':
            return file_perm == self.target_perm
        elif self.mode == 'all':
            return (file_perm & self.target_perm) == self.target_perm
        elif self.mode == 'any':
            return (file_perm & self.target_perm) != 0
        
        return False

class ExecutableExpression(FindExpression):
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return os.access(path, os.X_OK)

class ReadableExpression(FindExpression):
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return os.access(path, os.R_OK)

class WritableExpression(FindExpression):
    def evaluate(self, path: str, st: os.stat_result) -> bool:
        return os.access(path, os.W_OK)

class FindAction:
    """Base class for find actions"""
    def execute(self, path: str, st: os.stat_result) -> bool:
        raise NotImplementedError

class PrintAction(FindAction):
    def execute(self, path: str, st: os.stat_result) -> bool:
        print(path)
        return True

class Print0Action(FindAction):
    def execute(self, path: str, st: os.stat_result) -> bool:
        print(path, end='\0')
        return True

class LsAction(FindAction):
    def execute(self, path: str, st: os.stat_result) -> bool:
        # Format similar to ls -dils
        inode = st.st_ino
        blocks = st.st_blocks
        mode = stat.filemode(st.st_mode)
        nlinks = st.st_nlink
        size = st.st_size
        mtime = time.strftime('%b %d %H:%M', time.localtime(st.st_mtime))
        
        print(f"{inode:8d} {blocks:4d} {mode} {nlinks:3d} {size:8d} {mtime} {path}")
        return True

class DeleteAction(FindAction):
    def execute(self, path: str, st: os.stat_result) -> bool:
        try:
            if stat.S_ISDIR(st.st_mode):
                os.rmdir(path)
            else:
                os.unlink(path)
            return True
        except OSError:
            return False

class ExecAction(FindAction):
    def __init__(self, command: List[str], use_shell: bool = False):
        self.command = command
        self.use_shell = use_shell
    
    def execute(self, path: str, st: os.stat_result) -> bool:
        # Replace {} with the path
        cmd = []
        for arg in self.command:
            if arg == '{}':
                cmd.append(path)
            else:
                cmd.append(arg)
        
        try:
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

class FindParser:
    def __init__(self):
        self.tokens = []
        self.pos = 0
    
    def parse(self, args: List[str]) -> tuple:
        """Parse command line arguments and return (paths, expression, actions, options)"""
        self.tokens = args
        self.pos = 0
        
        paths = []
        options = {}
        
        # Parse paths (everything before first expression)
        while self.pos < len(self.tokens) and not self._is_expression(self.tokens[self.pos]):
            paths.append(self.tokens[self.pos])
            self.pos += 1
        
        # Default path is current directory
        if not paths:
            paths = ['.']
        
        # Parse options and expression
        expression = None
        actions = []
        
        if self.pos < len(self.tokens):
            expression, actions, options = self._parse_expression()
        
        # Default action is print
        if not actions:
            actions = [PrintAction()]
        
        return paths, expression or TrueExpression(), actions, options
    
    def _is_expression(self, token: str) -> bool:
        """Check if token is a find expression"""
        return token.startswith('-') or token == '(' or token == '!' or token == ')'
    
    def _parse_expression(self) -> tuple:
        """Parse the expression part"""
        options = {}
        actions = []
        
        # First, extract global options
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            
            if token in ['-maxdepth', '-mindepth']:
                if self.pos + 1 >= len(self.tokens):
                    raise ValueError(f"{token} requires an argument")
                options[token[1:]] = int(self.tokens[self.pos + 1])
                self.pos += 2
            elif token in ['-depth', '-follow']:
                options[token[1:]] = True
                self.pos += 1
            else:
                break
        
        # Parse the main expression
        expr = self._parse_or_expression()
        
        # Extract actions from the expression
        expr, actions = self._extract_actions(expr)
        
        return expr, actions, options
    
    def _parse_or_expression(self) -> FindExpression:
        """Parse OR expressions (lowest precedence)"""
        left = self._parse_and_expression()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos] in ['-o', '-or']:
            self.pos += 1
            right = self._parse_and_expression()
            left = OrExpression(left, right)
        
        return left
    
    def _parse_and_expression(self) -> FindExpression:
        """Parse AND expressions"""
        left = self._parse_unary_expression()
        
        while (self.pos < len(self.tokens) and 
               self.tokens[self.pos] not in ['-o', '-or', ')', ','] and
               not self._is_action(self.tokens[self.pos])):
            
            if self.tokens[self.pos] in ['-a', '-and']:
                self.pos += 1
            
            right = self._parse_unary_expression()
            left = AndExpression(left, right)
        
        return left
    
    def _parse_unary_expression(self) -> FindExpression:
        """Parse unary expressions (NOT, parentheses, tests)"""
        if self.pos >= len(self.tokens):
            return TrueExpression()
        
        token = self.tokens[self.pos]
        
        if token in ['!', '-not']:
            self.pos += 1
            expr = self._parse_unary_expression()
            return NotExpression(expr)
        
        elif token == '(':
            self.pos += 1
            expr = self._parse_or_expression()
            if self.pos >= len(self.tokens) or self.tokens[self.pos] != ')':
                raise ValueError("Missing closing parenthesis")
            self.pos += 1
            return expr
        
        else:
            return self._parse_test()
    
    def _parse_test(self) -> FindExpression:
        """Parse test expressions"""
        if self.pos >= len(self.tokens):
            return TrueExpression()
        
        token = self.tokens[self.pos]
        
        if token == '-name':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-name requires an argument")
            pattern = self.tokens[self.pos]
            self.pos += 1
            return NameExpression(pattern, True)
        
        elif token == '-iname':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-iname requires an argument")
            pattern = self.tokens[self.pos]
            self.pos += 1
            return NameExpression(pattern, False)
        
        elif token in ['-path', '-wholename']:
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError(f"{token} requires an argument")
            pattern = self.tokens[self.pos]
            self.pos += 1
            return PathExpression(pattern, True)
        
        elif token in ['-ipath', '-iwholename']:
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError(f"{token} requires an argument")
            pattern = self.tokens[self.pos]
            self.pos += 1
            return PathExpression(pattern, False)
        
        elif token == '-type':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-type requires an argument")
            file_type = self.tokens[self.pos]
            self.pos += 1
            return TypeExpression(file_type)
        
        elif token == '-size':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-size requires an argument")
            size_spec = self.tokens[self.pos]
            self.pos += 1
            return SizeExpression(size_spec)
        
        elif token in ['-mtime', '-ctime', '-atime']:
            time_type = token[1:]
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError(f"{token} requires an argument")
            time_spec = self.tokens[self.pos]
            self.pos += 1
            return TimeExpression(time_spec, time_type)
        
        elif token == '-empty':
            self.pos += 1
            return EmptyExpression()
        
        elif token == '-regex':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-regex requires an argument")
            pattern = self.tokens[self.pos]
            self.pos += 1
            return RegexExpression(pattern, True)
        
        elif token == '-iregex':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-iregex requires an argument")
            pattern = self.tokens[self.pos]
            self.pos += 1
            return RegexExpression(pattern, False)
        
        elif token == '-perm':
            self.pos += 1
            if self.pos >= len(self.tokens):
                raise ValueError("-perm requires an argument")
            perm_spec = self.tokens[self.pos]
            self.pos += 1
            return PermExpression(perm_spec)
        
        elif token == '-executable':
            self.pos += 1
            return ExecutableExpression()
        
        elif token == '-readable':
            self.pos += 1
            return ReadableExpression()
        
        elif token == '-writable':
            self.pos += 1
            return WritableExpression()
        
        elif token == '-true':
            self.pos += 1
            return TrueExpression()
        
        elif token == '-false':
            self.pos += 1
            return FalseExpression()
        
        else:
            # Unknown test, treat as true and don't consume
            return TrueExpression()
    
    def _is_action(self, token: str) -> bool:
        """Check if token is an action"""
        return token in ['-print', '-print0', '-ls', '-delete', '-exec', '-execdir', '-ok', '-okdir']
    
    def _extract_actions(self, expr: FindExpression) -> tuple:
        """Extract actions from remaining tokens"""
        actions = []
        
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            
            if token == '-print':
                actions.append(PrintAction())
                self.pos += 1
            
            elif token == '-print0':
                actions.append(Print0Action())
                self.pos += 1
            
            elif token == '-ls':
                actions.append(LsAction())
                self.pos += 1
            
            elif token == '-delete':
                actions.append(DeleteAction())
                self.pos += 1
            
            elif token in ['-exec', '-execdir']:
                self.pos += 1
                command = []
                while self.pos < len(self.tokens) and self.tokens[self.pos] != ';':
                    command.append(self.tokens[self.pos])
                    self.pos += 1
                
                if self.pos >= len(self.tokens):
                    raise ValueError(f"{token} command must end with ';'")
                
                self.pos += 1  # Skip ';'
                actions.append(ExecAction(command))
            
            else:
                break
        
        return expr, actions

class Find:
    def __init__(self):
        self.parser = FindParser()
    
    def run(self, args: List[str]) -> int:
        """Main entry point"""
        try:
            if '--help' in args:
                self._print_help()
                return 0
            
            if '--version' in args:
                self._print_version()
                return 0
            
            paths, expression, actions, options = self.parser.parse(args)
            
            for path in paths:
                self._find_in_path(path, expression, actions, options)
            
            return 0
            
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(f"find: {e}", file=sys.stderr)
            return 1
    
    def _find_in_path(self, start_path: str, expression: FindExpression, 
                      actions: List[FindAction], options: dict):
        """Find files in a given path"""
        maxdepth = options.get('maxdepth', float('inf'))
        mindepth = options.get('mindepth', 0)
        depth_first = options.get('depth', False)
        
        try:
            for path, depth in self._walk_path(start_path, maxdepth, depth_first):
                if depth < mindepth:
                    continue
                
                try:
                    st = os.lstat(path)
                    
                    if expression.evaluate(path, st):
                        for action in actions:
                            if not action.execute(path, st):
                                break
                
                except (OSError, PermissionError):
                    # Skip files we can't stat
                    continue
        
        except (OSError, PermissionError) as e:
            print(f"find: '{start_path}': {e}", file=sys.stderr)
    
    def _walk_path(self, path: str, maxdepth: float, depth_first: bool) -> Iterator[tuple]:
        """Walk directory tree, yielding (path, depth) tuples"""
        def _walk_recursive(current_path: str, current_depth: int) -> Iterator[tuple]:
            if current_depth > maxdepth:
                return
            
            if not depth_first:
                yield current_path, current_depth
            
            try:
                if os.path.isdir(current_path) and not os.path.islink(current_path):
                    entries = sorted(os.listdir(current_path))
                    for entry in entries:
                        entry_path = os.path.join(current_path, entry)
                        yield from _walk_recursive(entry_path, current_depth + 1)
            except (OSError, PermissionError):
                pass
            
            if depth_first:
                yield current_path, current_depth
        
        yield from _walk_recursive(path, 0)
    
    def _print_help(self):
        """Print help message"""
        print("""Usage: find.py [-H] [-L] [-P] [-Olevel] [-D debugopts] [path...] [expression]

Default path is the current directory; default expression is -print.
Expression may consist of: operators, options, tests, and actions.

Operators (decreasing precedence; -and is implicit where no others are given):
      ( EXPR )   ! EXPR   -not EXPR   EXPR1 -a EXPR2   EXPR1 -and EXPR2
      EXPR1 -o EXPR2   EXPR1 -or EXPR2

Normal options (always true, specified before other expressions):
      -depth -maxdepth LEVELS -mindepth LEVELS

Tests (N can be +N or -N or N):
      -atime N -ctime N -empty -executable -false -mtime N -name PATTERN
      -path PATTERN -perm [-/]MODE -readable -regex PATTERN -size N[bcwkMG]
      -true -type [bcdpfls] -writable
      -iname PATTERN -ipath PATTERN -iregex PATTERN

Actions:
      -delete -exec COMMAND ; -ls -print -print0

Other common options:
      --help                   display this help and exit
      --version                output version information and exit
""")
    
    def _print_version(self):
        """Print version information"""
        print("find.py 1.0.0")
        print("A Python implementation of the Unix find command")

def main():
    """Entry point"""
    find = Find()
    sys.exit(find.run(sys.argv[1:]))

if __name__ == '__main__':
    main()
