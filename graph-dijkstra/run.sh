#!/bin/sh

# example command: ./run.sh 20 length

N=$(($(wc -l ../cameras/cameras.csv | awk '{ print $1 }')-1));
K=$(perl -w -e "use POSIX; print ceil($N/$1), qq{\n}");
rm out/log-*;
rm out/pathes-$2-*;

for i in $(seq $1);
do
    (python cameras_shortest_path.py --start $(((i-1)*K)) --length $K --weight $2 &); 
done