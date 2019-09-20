#!/bin/bash
# Bash script meant to be run in a directory containing FeatureService seed audio files

# Default spectro path is in ../Scripts
GEN_SPECTRO_PATH=../Scripts/gen_spectro.py
# Tiling level 6 makes for a x32 zoom, level 5 is x16 and so on
TILING_LEVEL=6

# make_spectros(audio_file, nfft, winsize, overlap)
function make_spectros() {
  basename=${1%.*}
  folder=$basename/nfft=$2\ winsize=$3\ overlap=$4;
  mkdir -p "$folder";
  echo "Making spectros for $1 in folder $folder"
  python3 $GEN_SPECTRO_PATH -t $TILING_LEVEL -w $3 -n $2 -o $4 $1 "$folder/$basename";
}

# make_zip(folder_name)
function make_zip() {
  cd $1;
  tar -cvzf ../$1.tgz *;
  cd ..;
  rm -rf $1;
}

# SPM
# 1-winsize = 1024
# 1-nfft = 2048
# 1-overlap = 0.5
# 2-winsize = 4096
# 2-nfft = 4096
# 2-overlap = 0.5
for f in spm*.wav; do
  make_spectros $f 2048 1024 0.5;
  make_spectros $f 4096 4096 0.5;
  basename=${f%.*};
  make_zip $basename;
done

# DCLDE2015 HF
# 1-winsize = 1024
# 1-nfft = 1024
# 1-overlap = 0.5
# 2-winsize = 4096
# 2-nfft = 4096
# 2-overlap = 0.5
for f in 0*.wav; do
  make_spectros $f 1024 1024 0.5;
  make_spectros $f 4096 4096 0.5;
  basename=${f%.*};
  make_zip $basename;
done

# DCLDE2015 LF
# 1-winsize = 1024
# 1-nfft = 2048
# 1-overlap = 0.5
# 2-winsize = 4096
# 2-nfft = 4096
# 2-overlap = 0.5
for f in out*.wav; do
  make_spectros $f 2048 1024 0.5;
  make_spectros $f 4096 4096 0.5;
  basename=${f%.*};
  make_zip $basename;
done
