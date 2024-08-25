"""
Trimmed file which contains some utility python functions I carry with me.
Don't expect quality.
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""

from os.path import exists
from math import floor
from requests import get

# Returns whether the given file exists. If create is True, creates the file
# Returns True if the file already existed, False otherwise.
def ensure_file_exists(file_path:str, create = False):
    if exists(file_path):
        return True
    else:
        if create:
            with open(file_path, "x"):
                pass
        return False

# Read something from the given file. This returns None if the file doesn't exist.
def read_file_contents(file_path:str,
                       lines = False,
                       encoding = "utf-8",
                       read_mode = "r"):
    if not ensure_file_exists(file_path):
        return None
    if "b" in read_mode:
        encoding = None # Binary files do not take encoding arguments
    else:
        file = open(file = file_path, mode = read_mode, encoding = encoding)
        if lines:
            return file.readlines()
        else:
            return file.read()

# Write out some string to the file path given. This will create the file if it does not yet exist.
def write_file_contents(file_path:str,
                        contents:str,
                        write_mode = "w"):
    ensure_file_exists(file_path, create = True)
    if (not "w" in write_mode) and (not "a" in write_mode):
        print(f"WARN: No valid 'w' or 'a' mode passed to write_mode {write_mode}. File writing will probably fail!")
    with open(file = file_path, mode = write_mode, errors="ignore") as file:
        file.write(contents)

# Write out a python list to a given file. Will cast each content to a string unless string_method is provided.
# Delimiter is newlines by default
def write_list_contents(file_path:str,
                        py_list:list,
                        delimiter = "\n",
                        string_method = str):
    outfile_contents = ""
    for item in py_list:
        string_item = string_method(item)
        outfile_contents += f"{string_item}{delimiter}"
    write_file_contents(file_path, outfile_contents)

def plural(n:int|float) -> str:
    return "s" if n != 1 else ''

def format_seconds_to_times(seconds:float|int) -> str:
    """This sucks ballz but it works so i dont fukin care"""
    if seconds == 0:
        return "0 seconds"

    # Largest to smallest denominator
    seconds_in_one_minute = 1 * 60
    seconds_in_one_hour = 60 * seconds_in_one_minute
    seconds_in_one_day = seconds_in_one_hour * 24
    seconds_in_one_week = seconds_in_one_day * 7
    seconds_in_one_year = seconds_in_one_day * 365.25 # Slightly innacurate, but i dont care
    seconds_in_one_month = seconds_in_one_day * (365.25/12) # Also slightly innacurate, and i still dont care

    years = floor(seconds/seconds_in_one_year)
    seconds -= years * seconds_in_one_year

    months = floor(seconds/seconds_in_one_month)
    seconds -= months * seconds_in_one_month

    weeks = floor(seconds/seconds_in_one_week)
    seconds -= weeks * seconds_in_one_week

    days = floor(seconds/seconds_in_one_day)
    seconds -= days * seconds_in_one_day

    hours = floor(seconds/seconds_in_one_hour)
    seconds -= hours * seconds_in_one_hour

    minutes = floor(seconds/seconds_in_one_minute)
    seconds -= minutes * seconds_in_one_minute

    # and then seconds is left as it ought to be
    seconds = floor(seconds)

    toformat = [[years, "year"], [months, "month"], [weeks, "week"], [days, "day"], [hours, "hour"], [minutes, "minute"], [seconds, "second"]]
    output_str = ""
    for num_unit, unit in toformat:
        if num_unit == 0:
            continue
        output_str += f"{num_unit} {unit}{plural(num_unit)}, "
    output_str = output_str.rstrip(", ")
    return output_str

def make_request(url, write = True, outfile:str = "general_api_output.txt", encoding="utf-8", method = "a", params = {}):
    response = get(url, params)
    decoded_content = response.content.decode(encoding, errors="ignore")
    if (write):
        write_file_contents(outfile, decoded_content, method)
    return decoded_content, response.status_code

def get_request_url(request_type):
    from config import request_urls, api_url
    if request_type not in request_urls.keys():
        raise NotImplementedError(f"{request_type} not implemented into config dict request_urls")
    return f"{api_url}{request_urls[request_type]}"