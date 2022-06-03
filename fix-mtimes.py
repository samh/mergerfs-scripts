#!/usr/bin/env python3
"""
When initially copying from my old DrivePool, I neglected to preserve the
mtime in some cases.

I don't care to re-copy, because I've already done a bit of cleanup
(e.g. permissions, deleting junk), so try to just update the mtime
for paths that exist in both locations.
"""
import argparse
import os
import time


def main():
    parser = argparse.ArgumentParser(
        description="Copy mtimes from one set of paths to another",
    )
    parser.add_argument(
        "-f",
        "--from",
        dest="from_path",
        required=True,
        help="Source tree",
    )
    parser.add_argument(
        "-t",
        "--to",
        dest="to_path",
        required=True,
        help="Destination tree",
    )
    parser.add_argument(
        '-e',
        '--execute',
        action='store_true',
        help="Actually run (otherwise it's a dry run)",
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help="Show more details",
    )
    args = parser.parse_args()

    def timestr(secs):
        return time.strftime("%x %X", time.localtime(secs))

    changed_count = 0

    def copy_times(src_path_absolute):
        relative_path = os.path.relpath(src_path_absolute, args.from_path)
        # print(f"rel path: {relative_path}")
        dest_path_absolute = os.path.join(args.to_path, relative_path)
        # print(f"dest path abs: {dest_path_absolute}")
        if os.path.exists(dest_path_absolute):
            from_stat = os.stat(src_path_absolute)
            to_stat = os.stat(dest_path_absolute)
            # Only copy if source time is older
            # (we are trying to fix times that are too new)
            if from_stat.st_mtime < to_stat.st_mtime:
                print(f"Copying times for {relative_path}")
                # Show what we are changing from (current dest time, which
                # will be overwritten)
                print(f"  {timestr(to_stat.st_mtime)} -> {timestr(from_stat.st_mtime)}")
                nonlocal changed_count
                changed_count += 1
                if args.execute:
                    os.utime(
                        dest_path_absolute,
                        (from_stat.st_atime, from_stat.st_mtime),
                    )
            else:
                if args.verbose:
                    print(f"Times unchanged for {relative_path}")
                    print(
                        f"  {timestr(to_stat.st_mtime)}"
                        f" -> {timestr(from_stat.st_mtime)}",
                    )

    for (dirname, dirnames, filenames) in os.walk(args.from_path):
        fulldirpath = os.path.join(args.from_path, dirname)
        # print(dirname)
        # print(f"full dir: {fulldirpath}")
        # print(f"rel dir: {os.path.relpath(dirname, args.from_path)}")
        copy_times(os.path.relpath(dirname, args.from_path))
        # check_consistancy(fulldirpath,verbose)
        for filename in filenames:
            fullpath = os.path.join(fulldirpath, filename)
            # print(f"full path: {fullpath}")
            # print(filename)
            copy_times(fullpath)
            # check_consistancy(fullpath, verbose)

    print(f"Changed: {changed_count} files{'' if args.execute else ' (DRY-RUN)'}")


if __name__ == '__main__':
    main()
