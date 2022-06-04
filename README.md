# MergerFS Scripts
These are my personal scripts used to manage my MergerFS storage.

## Scripts
### `mergerfs-dedup.py`
This is a "fork" of `mergerfs.dedup` from
[mergerfs-tools](https://github.com/trapexit/mergerfs-tools). I changed
the include/exclude patterns to match against the full path.

### `mergerfs-drivepool-check.py`
I used this to look for files that existed on multiple drives and compare
them, to make sure there was no corruption (I didn't find any).
It is based on `mergerfs.fsck` from
[mergerfs-tools](https://github.com/trapexit/mergerfs-tools).

I don't intend to use this long-term; I would rely on the corruption
checking in btrfs or something like
[scorch](https://github.com/trapexit/scorch).

### `fix-mtimes.py`
I used this when moving files from older storage. I had initially copied
some of the files without preserving timestamps, so I used this script to
fix them.
It copies access and modifications times from one directory tree to
another (only for those files that exist in both).
