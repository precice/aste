

python3 gatherstats.py -o testcases/$1/cases/ -f $1.csv
python3 plot.py -f $1.csv -o $1
