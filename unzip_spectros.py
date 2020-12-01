# Script meant to be used in Docker/volumes/annotator_resources/png to unzip spectros tgz

import os, json

file_line = ""
with open("../../db_seeds/init.js", "r") as f:
    file_line = [line for line in f.readlines() if "filename" in line][0]

file_to_id = {record["filename"]:str(record["id"]) for record in json.loads(file_line.replace("'", '"'))}

tgzs = [filename for filename in os.listdir() if filename.endswith(".tgz")]

for tgz in tgzs:
    target = file_to_id[tgz[:-3] + "wav"]
    os.mkdir(target)
    os.system(f"tar zxf {tgz} -C {target}")
    os.remove(tgz)
