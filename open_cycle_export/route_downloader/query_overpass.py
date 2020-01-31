import os
import re
import json
import os.path
import hashlib
import logging

import requests
import overpass

api = overpass.API(timeout=600)

logger = logging.getLogger(__name__)


def remove_whitespace(string):
    return re.sub(r"\s*", "", string)


def minify_query(query):
    # TODO: Remove commented lines
    strings = re.findall(r"\"[^\"]+\"", query)
    strings_without_spaces = [remove_whitespace(string) for string in strings]
    query = remove_whitespace(query)
    # Restore all strings to their original (with spaces)
    for string, string_without_spaces in zip(strings, strings_without_spaces):
        query = query.replace(string_without_spaces, string)
    return query


def hash_string(string):
    byte_array = bytes(string, "utf8")
    return hashlib.sha1(byte_array).digest().hex()


def get_cache_path(query_hash):
    cache_folder = ".cache"
    os.makedirs(cache_folder, exist_ok=True)
    return os.path.join(cache_folder, "{}.json".format(query_hash))


def query_overpass(query, verbosity="body", responseformat="geojson"):
    minified_query = minify_query(query)
    query_hash = hash_string(minified_query + verbosity + responseformat)
    cache_path = get_cache_path(query_hash)
    try:
        data = json.load(open(cache_path))
        logger.info("return cached result")
        return data
    except:
        logger.info("query overpass")
        kwargs = dict(verbosity=verbosity, responseformat=responseformat)
        data = api.get(minified_query, **kwargs)
        json.dump(data, open(cache_path, "w"))
        return data
