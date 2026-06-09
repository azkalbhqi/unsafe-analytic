# Packages
import os
from os.path import join
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
import requests
import json
from zipfile import ZipFile
import sys
import time
import unsafe.files as unfile
import unsafe.const as unconst 

"""
Define our utils
"""

# The get_dir helper function
# For a list of string tokens, we
# are returning a filepath and filename
# The last string token is most of the filename
# If the first token is api, we need to use the exts dict
# and append it to the last string token
# If the first token is url, we need to use the endpoint
# that is passed here to get the exact ext we are downloading
def get_dir(str_tokens, endpoint, fr, api_ext):
    # Get wildcard (FIPS, STATE_FIPS, NATION)
    wcard_type = str_tokens[0]
    # Replace wcard_type with wcard_name
    # The idea is that we want the directory
    # names to be generic, so that it scales
    # better. In practice this means that
    # instead of writing out a file to
    # a directory like
    # raw/exp/nsi.pqt
    # we would do raw/{FIPS}/exp/nsi.pqt
    # where the script that does downloading
    # or unzipping, etc has FIPS passed
    # in as an argument...
    wcard_name = "{" + wcard_type + "}"

    # Get url or api type
    end_type = str_tokens[1]
    # Get most of the filename
    file_pre = str_tokens[-1]
    # Join the middle tokens as a filepath
    mid_dirs = "/".join(str_tokens[2:-1])

    # Implement the api vs. url processing
    if end_type == "api":
        # For example, file_pre will be something like
        # "nsi" which is also our key in the exts dict
        # for the ext we need to use
        filename = file_pre + api_ext[file_pre]
    else:
        # Ext is after the last '.' character
        url_ext = endpoint.split(".")[-1]
        filename = file_pre + "." + url_ext

    # Now join the raw directory with the
    # wildcard name and mid_dirs
    filepath = join(fr, mid_dirs, wcard_name, filename)

    # Return this directory path and the filename w/ extension
    return filepath


# Helper function to process
# the DOWNLOAD dataframe for use in
# both the dwnld_out_files function
# and when downloading files
def process_file(file):
    # The name follows format like
    # county_api_exp_nsi
    # which we will use to get
    # file directories
    name = file[0]
    # The endpoint is what we're going to
    # put into a requests call
    endpoint = file[1]
    # Split name
    # Like county_api_exp_nsi
    str_tokens = name.split("_")

    return str_tokens, endpoint

# The download_url helper function
def download_url(url, save_path, chunk_size=1024*1024, retries=5):
    headers = {"Accept-Encoding": "identity"}
    for attempt in range(1, retries + 1):
        try:
            print(f"Downloading (attempt {attempt}/{retries}): {url}")
            r = requests.get(url, headers=headers, stream=True, timeout=(15, 60))
            r.raise_for_status()
            content_length = r.headers.get('Content-Length')
            total_bytes = int(content_length) if content_length is not None else None
            
            downloaded = 0
            with open(save_path, "wb") as fd:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    fd.write(chunk)
                    downloaded += len(chunk)
                    if total_bytes:
                        percent = (downloaded / total_bytes) * 100
                        sys.stdout.write(f"\r  Progress: {downloaded / (1024*1024):.2f} MB / {total_bytes / (1024*1024):.2f} MB ({percent:.1f}%)")
                    else:
                        sys.stdout.write(f"\r  Progress: {downloaded / (1024*1024):.2f} MB")
                    sys.stdout.flush()
            print() # Move to next line after loop
            
            if total_bytes is not None:
                actual_size = os.path.getsize(save_path)
                if actual_size < total_bytes:
                    raise IOError(f"Truncated download: got {actual_size} bytes, expected {total_bytes}")
            
            # Verify if it's a valid zip if it has .zip extension
            if save_path.endswith(".zip"):
                with ZipFile(save_path, "r") as zf:
                    if zf.testzip() is not None:
                        raise IOError("Downloaded zip file is corrupt (testzip failed)")
            
            # If we reached here, download is successful and complete
            return
        except Exception as e:
            print(f"\nAttempt {attempt}/{retries} failed for {url}: {e}")
            if attempt == retries:
                raise
            time.sleep(2 ** attempt) # Exponential backoff


# The download_api helper function
# TODO: it may make sense to have some more
# configuration data about
# downloading from different apis
# so want to split this from the download_url
# function
def download_api(url, save_path, chunk_size=1024*1024, retries=5):
    headers = {"Accept-Encoding": "identity"}
    for attempt in range(1, retries + 1):
        try:
            print(f"Downloading API data (attempt {attempt}/{retries}): {url}")
            r = requests.get(url, headers=headers, stream=True, timeout=(15, 60))
            r.raise_for_status()
            content_length = r.headers.get('Content-Length')
            total_bytes = int(content_length) if content_length is not None else None
            
            downloaded = 0
            with open(save_path, "wb") as fd:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    fd.write(chunk)
                    downloaded += len(chunk)
                    if total_bytes:
                        percent = (downloaded / total_bytes) * 100
                        sys.stdout.write(f"\r  Progress: {downloaded / (1024*1024):.2f} MB / {total_bytes / (1024*1024):.2f} MB ({percent:.1f}%)")
                    else:
                        sys.stdout.write(f"\r  Progress: {downloaded / (1024*1024):.2f} MB")
                    sys.stdout.flush()
            print() # Move to next line after loop
            
            if total_bytes is not None:
                actual_size = os.path.getsize(save_path)
                if actual_size < total_bytes:
                    raise IOError(f"Truncated download: got {actual_size} bytes, expected {total_bytes}")
            
            # Verify if it's a valid JSON by trying to read start/end chars
            with open(save_path, "r", encoding="utf-8") as fd:
                fd.seek(0, 2)
                file_size = fd.tell()
                if file_size == 0:
                    raise IOError("Downloaded JSON file is empty")
                
                # Read first char
                fd.seek(0)
                first_char = fd.read(1).strip()
                while not first_char and fd.tell() < file_size:
                    first_char = fd.read(1).strip()
                
                # Read last char
                fd.seek(max(0, file_size - 100))
                last_chars = fd.read().strip()
                
                if first_char not in ('{', '[') or (last_chars and last_chars[-1] not in ('}', ']')):
                    raise IOError("Downloaded JSON file is corrupt/incomplete (invalid start/end characters)")
            
            # If we reached here, download is successful and complete
            return
        except Exception as e:
            print(f"\nAttempt {attempt}/{retries} failed for {url}: {e}")
            if attempt == retries:
                raise
            time.sleep(2 ** attempt) # Exponential backoff


# The download_raw function
# We are going to iterate through our
# DOWNLOAD dataframe and
# 1) clean the endpoint
# 2) get the out filepath
# 3) download the data
# 4) write it in the out_filepath
def download_raw(files, wcard_dict, fr, api_ext):
    for file in files.itertuples():
        # Get the str_tokens and endpoint from the dataframe row
        str_tokens, endpoint = process_file(file)
        
        # Check if the endpoint is a placeholder (like "null" or empty)
        if not endpoint or endpoint.lower() in ("null", "none"):
            print(f"Skipping placeholder endpoint: {'_'.join(str_tokens)}")
            continue

        # Get the out filepath
        # "Clean" it with the wcard_dict
        out_filepath = get_dir(str_tokens, endpoint, fr, api_ext)
        out_filepath = unfile.fill_wcard(out_filepath, wcard_dict)
        # "Clean" the endpoint with the wcard_dict
        endpoint = unfile.fill_wcard(endpoint, wcard_dict)

        # Make sure we can write out data to this filepath
        unfile.prepare_saving(out_filepath)

        # Check if file is already downloaded and non-empty
        if os.path.exists(out_filepath) and os.path.getsize(out_filepath) > 0:
            if out_filepath.endswith(".zip"):
                try:
                    with ZipFile(out_filepath, "r") as zf:
                        if zf.testzip() is None:
                            print("Already downloaded (valid zip): " + str(endpoint))
                            continue
                except Exception:
                    print("Corrupt/incomplete zip detected, re-downloading: " + str(endpoint))
                    pass
            else:
                print("Already downloaded: " + str(endpoint))
                continue

        # Download data with api or url call
        if str_tokens[1] == "api":
            # If api, call download_api helper function
            download_api(endpoint, out_filepath)
        else:
            # If url, call download_url helper function
            # and write file
            download_url(endpoint, out_filepath)

        # TODO log what is being done
        print("Downloaded from: " + str(endpoint))
