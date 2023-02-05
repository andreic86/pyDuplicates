# This is a script meant to find duplicated files by scanning directories offered on command line
# This is done by opening the files, creating a hash for each file and then listing duplicates
import argparse
import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime


# global dictionary containing all the SHAs and file paths per SHA
_sha = defaultdict(list)
# global list containing all the files to be checked
_files = []


def _parse_arguments():
    parser = argparse.ArgumentParser(description='Finds duplicated files in specified directories',
                                     prog='duplicateFinder')
    parser.add_argument('--dir', nargs='*', required=True,
                        help='Directory or directories to look into')
    parser.add_argument('--save-json', action='store_true', default=False,
                        help='Save found duplicates to a json file (results_$DATE.json)')
    parser.add_argument('--quiet', action='store_true', default=False,
                        help='Print no debug information in runtime. '
                             'Only prints the duplicate list or saves it to json.')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    return parser.parse_args()


def get_another_file():
    global _files
    if len(_files):
        return _files.pop()
    return None


def _calculate_sha(file):
    sha1 = hashlib.sha1()
    with open(file, 'rb') as f:
        while True:
            data = f.read(64 * 1024)  # 64Kb buffer size
            if not data:
                break  # read to end
            sha1.update(data)
    return sha1


def _find_files_in_dir(directory, quiet):
    files = []
    if not quiet:
        print(f"Will look into the following directory {directory}")
    for root, _, found_files in os.walk(directory):
        if ':\\$RECYCLE.BIN' in root:
            continue
        for file in found_files:
            files.append(os.path.join(root, file))
    if not quiet:
        print(f"Found a total of {len(files)} files in {directory}")
    return files


def _find_duplicated_files(args):
    global _files
    for dir in args.dir:
        _files = _files + _find_files_in_dir(dir, args.quiet)

    if not args.quiet:
        print(f"Found a total of {len(_files)}")
    count = 0

    for file in _files:
        count = count + 1
        if not args.quiet:
            print(f"{count}/{len(_files)} : Checking {file.encode('utf-8')}")
        # noinspection PyBroadException
        try:
            sha = _calculate_sha(file)
            _sha[sha.hexdigest()].append(file)
        except Exception:
            pass  # silently ignore
    duplicates = defaultdict(list)
    for sha in sorted(_sha.keys()):
        if len(_sha[sha]) > 1:
            duplicates[sha] = _sha[sha]
            if not args.save_json:
                print(f"Duplicated files found with sha {sha}:")
                for f in _sha[sha]:
                    size = round(os.path.getsize(f) / 1024 / 1024, 3)
                    tabs = '\t\t' if size < 100 else '\t'
                    print(f"    {size} MB {tabs}{f}")
    if len(duplicates) and args.save_json:
        now_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_json_name = f"results_{now_string}.json"
        with open(result_json_name, 'w') as duplicated_json:
            json.dump(duplicates, duplicated_json, indent=4)
            print(f"Saved {len(duplicates)} duplicate hits to {os.path.abspath(result_json_name)}.")
    if not args.save_json:
        print(f"Found a total of {len(duplicates)} duplicates!")


if __name__ == '__main__':
    arguments = _parse_arguments()
    start = datetime.now()
    _find_duplicated_files(arguments)
    if not arguments.quiet:
        took = datetime.now() - start
        print(f"It took {took} to find duplicates..")
