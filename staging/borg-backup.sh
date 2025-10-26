#!/bin/bash
# Author: Sidhant Dixit
# Source: https://borgbackup.readthedocs.io/en/stable/quickstart.html
# Noteable References
#   - Pipefail: https://stackoverflow.com/a/6872163/8926755
#   - Output Redirection:
#       https://stackoverflow.com/a/22095862/8926755
#
# TODO: Refactor to init borg repo if one doesn't exist for the user
#

BACKUP_DIR=/data/backups
BACKUP_SOURCE_DIR=$HOME
BORG_REPO=borg/$HOSTNAME-$USER
BORG_LOGS_DIR=borg/logs

# Helper functions and error handling
info() { printf "\n%s %s\n" "$( date )" "$*" >&2; }
trap 'echo $( date ) Backup interrupted >&2; exit 2' INT TERM

info "Checking if \"$BACKUP_DIR\" has a drive mounted on it"

# TODO: add a check to see if borg_repo exists before running command
if grep $BACKUP_DIR /etc/mtab > /dev/null 2>&1; then
    info "$BACKUP_DIR found on filesystem.."
    info "Initiating borg backup:"
    info "Source:           $BACKUP_SOURCE_DIR"
    info "Destination:      $BORG_REPO"
    info "Logfiles:         $BORG_LOGS_DIR"
    borg create                                             \
        --verbose                                           \
        --filter AME                                        \
        --list                                              \
        --stats                                             \
        --show-rc                                           \
        --compression lzma,9                                \
        --progress                                          \
        --exclude-caches                                    \
        --exclude "$HOME/.cache/"                           \
        --exclude "$HOME/.local/share/"                     \
        --exclude "$HOME/.config/borg/"                     \
        --exclude "$HOME/snap"                              \
        $BACKUP_DIR/$BORG_REPO/::{hostname}-{user}-{now:%Y-%m-%dT%H:%M:%S.%f} \
        $BACKUP_SOURCE_DIR 2>&1 |                           \
        tee -a $BACKUP_DIR/$BORG_LOGS_DIR/$HOSTNAME-$USER-backup.log

    set -o pipefail
    backup_exit=$?
    set +o pipefail

    info "Pruning repository"

    # Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
    # archives of THIS machine. The '{hostname}-*' matching is very important to
    # limit prune's operation to this machine's archives and not apply to
    # other machines' archives also:
    borg prune                          \
        --verbose                       \
        --list                          \
        --glob-archives '{hostname}-*'  \
        --show-rc                       \
        --keep-daily    7               \
        --keep-weekly   4               \
        --keep-monthly  6               \
        --keep-yearly   3               \
        $BACKUP_DIR/$BORG_REPO/ 2>&1 |  \
        tee -a $BACKUP_DIR/$BORG_LOGS_DIR/$HOSTNAME-$USER-prune.log

    set -o pipefail
    prune_exit=$?
    set +o pipefail

    # actually free repo disk space by compacting segments

    info "Compacting repository" 2>/dev/stdout | \
        tee -a $BACKUP_DIR/$BORG_LOGS_DIR/$HOSTNAME-$USER-compact.log
    info "Space used before compacting repo:"
    info "$(df -h $BACKUP_DIR/$BORG_REPO/)"

    borg compact                                            \
        $BACKUP_DIR/$BORG_REPO/ 2>&1 |                      \
        tee -a $BACKUP_DIR/$BORG_LOGS_DIR/$HOSTNAME-$USER-compact.log

    set -o pipefail
    compact_exit=$?
    set +o pipefail


    info "Completed compacting repository" 2>/dev/stdout | \
        tee -a $BACKUP_DIR/$BORG_LOGS_DIR/$HOSTNAME-$USER-compact.log
    info "Space used after compacting repo: "
    info "$(df -h $BACKUP_DIR/$BORG_REPO/)"

    # use highest exit code as global exit code
    global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))
    global_exit=$(( compact_exit > global_exit ? compact_exit : global_exit ))

    if [ ${global_exit} -eq 0 ]; then
       info "Backup, Prune, and Compact finished successfully"
    elif [ ${global_exit} -eq 1 ]; then
        info "Backup, Prune, and/or Compact finished with warnings"
    else
        info "Backup, Prune, and/or Compact finished with errors"
    fi

    exit ${global_exit}
else
    info "Could not find borg repo \"$BORG_REPO\" mounted on \"$BACKUP_DIR\""
    info "Exiting script without creating backup"
    # Exit with warning
    exit 1
fi
