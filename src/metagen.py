'''
Helper script for generating meta data files for datasets.

Throughout the script we're assuming the following structure 
of the directory that settings.PATH_LOCAL_DATA points to.

|-- datasets
|   |-- testdataset
|   |   |-- clean
|   |   |   `-- example.txt
|   |   |-- meta.yaml ----> this is where the output will reside
|   |   `-- raw
|   |       `-- example.html
|-- plot-output
|   `-- img.png
`-- results-cache
    `-- results.pickle
'''
import os
import sys
import re
import codecs

import yaml
from BeautifulSoup import BeautifulSoup
import argparse

import settings


class MetaGeneratorError(Exception):
    pass

def cleaneval(dataset_name):
    '''Meta data generator for cleaneval-ish datasets'''
    
    dataset_path = os.path.join(settings.PATH_LOCAL_DATA,'datasets' ,dataset_name)
    if not os.path.exists(dataset_path):
        raise MetaGeneratorError('Dataset does not exist: %s' % dataset_name)
    
    meta_data_list = [] # list to be returned containing meta data
    
    for raw_fileanme in os.listdir(os.path.join(dataset_path, 'raw')):
        with open(os.path.join(dataset_path, 'raw', raw_fileanme), 'r' ) as f:
            
            # validate raw names
            if not re.match(r'\d+.html', raw_fileanme):
                raise MetaGeneratorError('Raw filename not matching [number].html: %s' % raw_fileanme)
            # check for an existing clean file counterpart
            clean_filename = raw_fileanme.replace('.html', '') + '-cleaned.txt'
            if not os.path.exists(os.path.join(dataset_path, 'clean', clean_filename )):
                raise MetaGeneratorError('No existing clean file counterpart for %s' % raw_fileanme)
            
            # get meta data from <text ...> tag
            soup = BeautifulSoup(f.read())
            text_tag = soup.find('text')
            encoding = text_tag['encoding']
            
            # get a safe encoding name
            try:
                codec = codecs.lookup(encoding)
            except LookupError:
                safe_encoding = None
            else:
                safe_encoding = codec.name
                
            
            meta_data_list.append(dict(
                url = None,
                encoding = safe_encoding,
                raw = raw_fileanme,
                clean = clean_filename,
            ))
            
    return yaml.dump(meta_data_list, default_flow_style=False)

def main():
    # sys argument parsing trough argparse
    parser = argparse.ArgumentParser(description = 'Tool for generating meta data files for datasets')
    parser.add_argument('dataset_type', choices = ['cleaneval'], help = 'dataset type e.g. cleaneval' )# only cleaneval choice for now
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-p','--path', help = 'path to the output file (optional) or store in the intended location')
    parser.add_argument('-v','--verbose', action = 'store_true')
    args = parser.parse_args()
    
    # printing arguments
    print 'dataset type: %s' % args.dataset_type
    print 'dataset name: %s' % args.dataset_name
    
    # validating path arguent
    if args.path and not os.path.exists(args.path):
        print 'error: path does not exist'
        sys.exit(-1)
    
    output_path = os.path.join(args.path, 'meta.yaml')  if args.path else \
    os.path.join(settings.PATH_LOCAL_DATA, 'datasets', args.dataset_name ,'meta.yaml') 
    print 'output path: %s' % output_path
    
    if args.dataset_type == 'cleaneval':

        try:
            yaml_output  = cleaneval(args.dataset_name)
        except MetaGeneratorError as e:
            # print any errors encountered during generating meta data
            print e
            sys.exit(-1)
        else:
            if args.verbose: print yaml_output
            
            with open(output_path ,'w') as f:
                f.write(yaml_output)

if __name__ == '__main__':
    main()


