#!/usr/bin/env python3

import logging
import os
import re
import subprocess
import sys
import uuid
from git import Repo


def log_info(msg):
    logging.info('[pre-push] > {}'.format(msg))

def log_debug(msg):
    logging.debug('[pre-push] > {}'.format(msg))

def run_cmd_args(cmd_args):
    logging.debug(' >>> {}'.format(' '.join(cmd_args)))
    proc = subprocess.run(cmd_args, encoding='utf-8', stdout=subprocess.PIPE)
    for line in proc.stdout.split('\n'):
        logging.debug(line)


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('git').setLevel(logging.WARNING)

    curdir = os.path.curdir
    repo = Repo(curdir)
    _git = repo.git

    changes_stashed = False

    _git.add('.')
    if repo.is_dirty():
        log_info('Saving all local changes in a temporary stash')
        stash_message = '[pre-push] Temporary stash, do not delete. <id: {}>'.format(uuid.uuid4().hex)
        log_debug(f'Message for temporary stash: {stash_message}')
        _git.stash('push', '-u', '-m', stash_message)
        changes_stashed = True

    xcode_project_name = 'PracticeRoom.xcodeproj'

    log_info('Running synx')
    run_cmd_args(['synx', '--prune', xcode_project_name])

    log_info('Running xunique')
    run_cmd_args(['xunique', xcode_project_name])

    if repo.is_dirty():
        log_info('Adding changes made by hook')
        _git.add(curdir)

        log_info('Committing changes made by hook')
        _git.commit('--no-verify', '-m', '[pre-push] Run synx and xunique')
    else:
        log_info('No changes were made by hook')
    
    if changes_stashed:
        log_info('Popping temporary stash')

        stash_ref_key = 'stash_ref'
        stash_message_escaped = re.escape(stash_message)
        stash_regex = re.compile('(?P<{}>stash@{{[0-9]+}}).*{}\n?'.format(stash_ref_key, stash_message_escaped))
        stash_list = _git.stash('list')

        log_debug('All stashes: \n{}'.format(stash_list))
        matching_stashes = stash_regex.findall(stash_list)

        log_debug(f'Found matching stashes: {matching_stashes}')

        num_of_matching_stashes = len(matching_stashes)
        assert num_of_matching_stashes > 0, f'Stash not found with message "{stash_message}"'
        assert num_of_matching_stashes == 1, f'More than one ({num_of_matching_stashes}) stash found with message "{stash_message}"'

        stash_ref = matching_stashes[0]

        log_debug(f'Popping "{stash_ref}"')
        _git.stash('pop', stash_ref)


if __name__ == '__main__':
    main()
