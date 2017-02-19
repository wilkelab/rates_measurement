#!/bin/bash
num_sim=30
site_dupl=100000
model='JC_equalf'

if [ ! -d "./hyphy/rates" ]; then
	mkdir ./hyphy/rates
fi

if [ ! -d "./hyphy/rates/raw_rates" ]; then
	mkdir ./hyphy/rates/raw_rates
fi

for br_len in `seq -f %.2f 0.02 0.02 0.52` 
do	 
	for i in $(seq 1 $num_sim) 
	do
		aln_tree_file=n2_bl${br_len}_${i}_aln_tree.txt
		rates_file=n2_bl${br_len}_${i}_${model}_rates.txt
		echo "INFILE = aln_tree_files/translated/${aln_tree_file}" > hyphy/setup.txt
		echo "OUTFILE = ../inferred_rates/raw_rates/translated/${rates_file}" >> hyphy/setup.txt
		echo "SITE_DUPL = ${site_dupl}" >> hyphy/setup.txt
		HYPHYMP hyphy/fitrates_${model}.bf
	done
done

