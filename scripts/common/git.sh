function git::is_inside_repo() {
    git rev-parse --git-dir &>/dev/null
}

function git::get_user_email() {
    git config user.email
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :