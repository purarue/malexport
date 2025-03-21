#!/usr/bin/env bash
# shell functions I use for my data
# these can be used in combination to filter/extract data
# a lot of them use https://github.com/stedolan/jq, so I'd
# recommend getting a bit familiar with that

mal_list() {
	local -a args=()
	if [ -z "${MAL_USERNAME}" ]; then
		echo "Set the 'MAL_USERNAME' environment variable to your account name" >&2
		return 1
	fi
	TYPE="${1:-anime}"
	DIR="${MALEXPORT_DIR:-${HOME}/.local/share/malexport}"
	if [ ! -d "${DIR}/${MAL_USERNAME}" ]; then
		echo "No data found for user '${MAL_USERNAME}'" >&2
		return 1
	fi
	if [ ! -f "${DIR}/${MAL_USERNAME}/${TYPE}list.json" ]; then
		echo "No ${TYPE}list.json found for user '${MAL_USERNAME}'" >&2
		return 1
	fi
	args+=("python" -m malexport parse list -s "${DIR}/${MAL_USERNAME}/${TYPE}list.json")
	# optional line-based caching using https://github.com/purarue/fzfcache
	if [[ -n "$LISTCACHED" ]]; then
		args=(fzfcache "${args[@]}")
	fi
	"${args[@]}"
}

mal_list_cached() {
	LISTCACHED=1 mal_list "${@}"
}

pickentry() {
	cmd='mal_list'
	if command -v fzfcache >/dev/null; then
		cmd='mal_list_cached'
	fi
	CHOSEN="$("$cmd" "${1}" | jq -r '"\(.id)|\(.title)"' | fzf)"
	[ -z "${CHOSEN}" ] && return 1
	echo "${CHOSEN}" | cut -d'|' -f1
}

openentry() {
	id=$(pickentry "${1}")
	[[ -z "$id" ]] && return 1
	python3 -m webbrowser -t "https://myanimelist.net/${1}/${id}"
}

animefzf() {
	openentry 'anime'
}

mangafzf() {
	openentry 'manga'
}

# filters the mal_list down to a particular status type
# mal_status 'Plan to Watch'
# mal_status 'Plan to Read' manga
mal_status() {
	MAL_USERNAME="$MAL_USERNAME" mal_list "${2:-anime}" | jq "select(.status == \"${1:-Completed}\")"
}

# uses xml since that's easier to update
mal_xml_status_ids() {
	local st mtype
	st="${1:-Watching}"
	mtype="${2:-anime}"
	malexport parse xml "${MALEXPORT_DIR}/${MAL_USERNAME}"/"${mtype}"list.xml | jq "$(printf '.entries | .[] | select(.status == "%s")' "$st")" -r | jq ".${mtype}_id" | sort
}

# e.g. mal_status Dropped | mal_filter_unscored | mal_describe
mal_filter_unscored() {
	jq 'select(.score != 0)'
}

mal_filter_type() {
	jq "select(.media_type == \"${1:-Movie}\")"
}

mal_sort_blobs() {
	jq -s "sort_by(.\"${1:-score}\") | .[]"
}

mal_filter_genre() {
	local genre
	genre="${1?:Pass name of Genre as first argument}"
	jq "select(.genres | .[] | .name | contains(\"${genre}\"))"
}

mal_filter_airing_status() {
	jq "select(.airing_status == \"${1:-Currently Airing}\")"
}

# given blobs of objects, describes each
# can be used like "mal_status 'Plan to Watch' | mal_describe"
mal_describe() {
	jq -r '"\(.id) \(.title) (\(.season.year)) \(.status) \(.score)/10"'
}

mal_club() {
	local club
	club="${1?:Pass club id as first argument}"
	curl -s "https://api.jikan.moe/v4/clubs/${club}/relations" | jq '.data.anime[].mal_id' | sort
}
