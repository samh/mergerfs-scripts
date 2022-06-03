#!/usr/bin/env python3
"""
Finds files that are on more than one drive and checks to make sure they
are the same (to detect e.g. silent disk corruption).

Based on "mergerfs.fsck" from mergerfs-tools.
"""
# Original copyright notice from mergerfs.fsck:
#
# Copyright (c) 2016, Antonio SJ Musumeci <trapexit@spawn.link>

# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.

# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import argparse
import ctypes
import errno
import io
import os
import subprocess
import sys

checked_count = 0
different_count = 0
different_files = []


_libc = ctypes.CDLL("libc.so.6",use_errno=True)
_lgetxattr = _libc.lgetxattr
_lgetxattr.argtypes = [ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t]
def lgetxattr(path,name):
    if type(path) == str:
        path = path.encode(errors='backslashreplace')
    if type(name) == str:
        name = name.encode(errors='backslashreplace')
    length = 64
    while True:
        buf = ctypes.create_string_buffer(length)
        res = _lgetxattr(path,name,buf,ctypes.c_size_t(length))
        if res >= 0:
            return buf.raw[0:res]
        else:
            err = ctypes.get_errno()
            if err == errno.ERANGE:
                length *= 2
            elif err == errno.ENODATA:
                return None
            else:
                raise IOError(err,os.strerror(err),path)


def ismergerfs(path):
    try:
        lgetxattr(path,"user.mergerfs.fullpath")
        return True
    except IOError as e:
        return False


def print_stats(Files,Stats):
    for i in range(0,len(Files)):
        print("  %i: %s" % (i,Files[i].decode(errors='backslashreplace')))
        data = ("   - uid: {0:5}; gid: {1:5}; mode: {2:6o}; "
                "size: {3:10}; mtime: {4}").format(
            Stats[i].st_uid,
            Stats[i].st_gid,
            Stats[i].st_mode,
            Stats[i].st_size,
            Stats[i].st_mtime)
        print (data)


def check_consistancy(fullpath,verbose):
    paths = lgetxattr(fullpath,"user.mergerfs.allpaths")
    if not paths:
        return
    paths = paths.split(b'\0')
    if len(paths) <= 1:
        return
    
    global checked_count
    checked_count += 1

    if verbose:
        print("%s" % fullpath)
    diff = subprocess.run(['diff', '-q'] + paths)
    if diff.returncode != 0:
        global different_count
        global different_files
        different_count += 1
        different_files.append(paths)
        stats = [os.stat(path) for path in paths]
        # print("%s" % fullpath)
        if verbose:
            print_stats(paths,stats)


def buildargparser():
    parser = argparse.ArgumentParser(description='audit a mergerfs mount for inconsistencies')
    parser.add_argument('dir',type=str,
                        help='starting directory')
    parser.add_argument('-v','--verbose',action='store_true',
                        help='print details of audit item')
    return parser


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,
                                  encoding='utf8',
                                  errors='backslashreplace',
                                  line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer,
                                  encoding='utf8',
                                  errors='backslashreplace',
                                  line_buffering=True)

    parser = buildargparser()
    args = parser.parse_args()

    args.dir = os.path.realpath(args.dir)
    if not ismergerfs(args.dir):
        print("%s is not a mergerfs directory" % args.dir)
        sys.exit(1)

    try:
        verbose = args.verbose
        for (dirname,dirnames,filenames) in os.walk(args.dir):
            fulldirpath = os.path.join(args.dir,dirname)
            #check_consistancy(fulldirpath,verbose)
            for filename in filenames:
                fullpath = os.path.join(fulldirpath,filename)
                check_consistancy(fullpath,verbose)
    except KeyboardInterrupt:
        pass
    except IOError as e:
        if e.errno == errno.EPIPE:
            pass
        else:
            raise

    print(f"Checked count: {checked_count}")
    print(f"Different count: {different_count}")
    if different_files:
        for file in different_files:
            print(file)
    sys.exit(0)


if __name__ == "__main__":
    main()
