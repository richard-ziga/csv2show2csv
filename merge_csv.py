from glob import glob

with open('singleDataFile.csv', 'a') as singleFile:
    for csvFile in glob('*.csv'):
        for line in open(csvFile, 'r'):
            singleFile.write(line)