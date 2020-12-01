#!/bin/bash
# Bash script meant to be run in a directory containing FeatureService seed audio files

# Default spectro path is in ../Scripts
export GEN_SPECTRO_PATH=gen_spectro.py
# Tiling level 6 makes for a x32 zoom, level 5 is x16 and so on
export TILING_LEVEL=6
# How many cores on machine to parallelize calculations (be careful about RAM consumption as well)
CORES=5

# make_spectros(audio_file, nfft, winsize, overlap)
function make_spectros() {
  basename=${1%.*}
  folder=$basename/nfft=$2\ winsize=$3\ overlap=$4\ cvr=$6;
  mkdir -p "$folder";
  echo "Making spectros for $1 in folder $folder"
  python3 $GEN_SPECTRO_PATH -t $TILING_LEVEL -w $3 -n $2 -o $4 -mw $5 -cvr=$6 $1 "$folder/$1";
}
export -f make_spectros

# make_zip(folder_name)
function make_zip() {
  cd $1;
  tar -cvzf ../$1.tgz *;
  cd ..;
  rm -rf $1;
}
export -f make_zip

# process_wave(wave_filename)
function process_wave() {
  make_spectros $1 2048 512 90 1 "-90:0" >> spectros.log;
  basename=${1%.*};
  make_zip $basename;
}
export -f process_wave

# RUN SPECTROS CALCULATIONS ON ALL WAVE FILES USING https://www.gnu.org/software/parallel/
ls *.wav | parallel --nice 10 -j $CORES process_wave
