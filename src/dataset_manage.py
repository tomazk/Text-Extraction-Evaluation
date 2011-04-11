'''
Helper script for generating meta data files and preprocessing datasets.

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
|   `-- ...
`-- results-cache
    `-- ...
'''
import os
import sys
import re
import codecs
import logging

import yaml
from BeautifulSoup import BeautifulSoup
import argparse

import settings

logger = logging.getLogger()

class MetaGeneratorError(Exception):
    pass

class PreprocessingError(Exception):
    pass
    
def _verify_args(args):
    # verify arguments provoded by argparse and
    # return the path to the output directory
    
    # printing arguments
    print 'dataset type: %s' % args.dataset_type
    print 'dataset name: %s' % args.dataset_name
    
    #validate dataset name
    if not os.path.exists( os.path.join(settings.PATH_LOCAL_DATA, 'datasets', args.dataset_name)):
        print 'error: this dataset does not exist'
        sys.exit(-1)
    
    # validate path argument
    if args.path and not os.path.exists(args.path):
        print 'error: path does not exist'
        sys.exit(-1)
        
    output_dir = args.path or os.path.join(settings.PATH_LOCAL_DATA, 'datasets', args.dataset_name)
    print 'output directory: %s' % output_dir
    return output_dir

    
def _get_attribute(tag, name):
    # params: BS tag and attribute name
    # return None or attribute value
    # takes care of encoding
    try: 
        return tag[name].encode('ascii', 'ignore')
    except KeyError:
        return None
    
def _remove_text_tag(html_string, filename):
    # Cleaneval has a <text> tag that wraps the whole html structure. This 
    # function removes it with a pessimistic regular expression because we don't 
    # want to mess with the rest of the structure with a parser
    
    # remove <text> at the beginning
    regex_beg = re.compile(r'(?P<text_tag>^(\s*)<(\s*)text((\s*)(id|title|encoding)(\s*)=(\s*)"(.*)")*(\s*)>)')
    match_start = regex_beg.match(html_string)
    if match_start:
        logger.debug('removing text tag in %s: %s', filename, match_start.group('text_tag'))
        html_string = regex_beg.sub('', html_string)
    else:
        raise PreprocessingError('no starting text tag in %s' % filename)

    # remove </text>
    regex_end = re.compile(r'(?P<closing_text_tag><(\s*)/(\s*)text(\s*)>(.*)$)')
    match_end = regex_end.search(html_string)
    if match_end:
        logger.debug('removing closing text tag in %s: %s', filename, match_end.group('closing_text_tag'))
        html_string = regex_end.sub('', html_string)
    else:
        raise PreprocessingError('no closing text tag in %s' % filename)
    
    return html_string

class BaseProcessor(object):
    
    def __init__(self, output_dir, dataset_name):   
        self._dataset_dir = os.path.join(settings.PATH_LOCAL_DATA,'datasets',dataset_name)
        self._output_dir = output_dir
    

class CleanevalProcessor(BaseProcessor):
    
    def _raw_filenames(self):       
        return os.listdir(os.path.join(self._dataset_dir, 'raw')) 
    
    def create_backups(self):
        # rename every unprocessed [number].html to [number].html.backup 
        
        for raw_filename in self._raw_filenames():
            
            # validate raw filename names
            if not re.match(r'^\d+.html$', raw_filename):
                logger.debug('skipping file %s for not matching cleaneval naming convention', raw_filename)
                continue
            
            raw_filename_path = os.path.join(self._dataset_dir, 'raw', raw_filename)
            backup_path = raw_filename_path + '.backup'
            logger.info('renaming %s to %s', raw_filename, raw_filename + '.backup')
            os.rename(raw_filename_path, backup_path)
    
    def generate_meta_data(self):
        
        meta_data_list = [] # list to be serialized
        
        for raw_filename in self._raw_filenames():
      
            # validate raw names
            if not re.match(r'^\d+.html.backup$', raw_filename):
                raise MetaGeneratorError('Raw filename backup not matching [number].html.backup: %s' % raw_filename)
            
            with open(os.path.join(self._dataset_dir, 'raw', raw_filename), 'r' ) as f:
                
                # check for an existing clean file counterpart
                clean_filename = raw_filename.replace('.html.backup', '') + '-cleaned.txt'
                if not os.path.exists(os.path.join(self._dataset_dir, 'clean', clean_filename )):
                    raise MetaGeneratorError('No existing clean file counterpart for %s' % raw_filename)
                
                # get meta data from <text ...> tag
                soup = BeautifulSoup(f.read())
                text_tag = soup.find('text')
                if text_tag == None:
                    raise MetaGeneratorError('No <text> tag in %s' % raw_filename)
                encoding = text_tag['encoding']
                
                # extract dataset specific meta-data and store it into a dict with
                # keys id, title, encoding
                # since we'll be removing the <text> tag from every document
                # we better store this attributes in it's original form in meta.yaml
                cleaneval_specific = {
                    'id': _get_attribute(text_tag, 'id'),
                    'title': _get_attribute(text_tag, 'title'),
                    'encoding': _get_attribute(text_tag, 'encoding'),
                }
                
                # get a safe encoding name
                try:
                    codec = codecs.lookup(encoding)
                except LookupError:
                    safe_encoding = None
                else:
                    safe_encoding = codec.name
                    
                logger.info('generating meta data for %s', raw_filename)
                meta_data_list.append(dict(
                    url = None,
                    raw_encoding = safe_encoding,
                    # acording to anotation guidelines of cleaneval 
                    # all cleaned text files are utf-8 encoded
                    clean_encoding = 'utf-8',
                    # we'll be generating [number].html in the preprocessing phase
                    raw = raw_filename.replace('.backup', ''), 
                    clean = clean_filename,
                    meta = cleaneval_specific
                ))
                
        # dump meta data
        with open(os.path.join(self._output_dir, 'meta.yaml'), 'w') as meta_file:
            meta_string = yaml.dump(meta_data_list, default_flow_style=False) 
            meta_file.write(meta_string)
            
    def preprocess(self):
        # remove all <text> tags
        # add missing <html><body> tags where needed
        
        for raw_filename in self._raw_filenames():
            # validate raw filename names
            if not re.match(r'^\d+.html.backup$', raw_filename):
                logger.debug('skipping file %s during preprocessing', raw_filename)
                continue
            
            with open(os.path.join(self._dataset_dir, 'raw', raw_filename), 'r' ) as f:
                html_string = _remove_text_tag(f.read(), raw_filename)
                
                soup = BeautifulSoup(html_string)
                if (not soup.find('html')) and (not soup.find('body')):
                    # no html no body tag
                    logger.warn('appending body and html tags to %s', raw_filename)
                    html_string = '<html><body>  %s  </body></html>' % html_string
                    
                elif (not soup.find('html')) or (not soup.find('body')):
                    # really weird case
                    raise PreprocessingError('this file has html tag or body tag but not both') 
                else:
                    logger.info('no tag appending on %s', raw_filename)
                
                output_filename = raw_filename.replace('.backup','')
                logger.debug('preprocesing complete: %s ---> %s',raw_filename,output_filename)
                with open(os.path.join(self._dataset_dir, 'raw', output_filename) ,'w') as output:
                    output.write(html_string)
                    
class GooglenewsProcessor(BaseProcessor):
    
    def generate_meta_data(self):
        pass
                
        
def main():
    # sys argument parsing trough argparse
    parser = argparse.ArgumentParser(description = 'Tool for generating meta data files and cleanup preprocessing regarding datasets')
    parser.add_argument('dataset_type', choices = ['cleaneval','gogole-news'], help = 'dataset type e.g. cleaneval' )# only cleaneval choice for now
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-p','--path', help = 'path to the meta data output file and .log file (uses the default path if not provided)')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    args = parser.parse_args()
    
    # get the ouput direcotry - this is where the .yaml and .log file will reside
    output_dir = _verify_args(args)
    
    # now we can initialize logging
    print 'log: %s' % os.path.join(output_dir, 'preproc.log')
    logging.basicConfig(filename= os.path.join(output_dir, 'preproc.log'), level=logging.DEBUG)
    
    # add a console handler to root logger if user provides a --verbose flag
    if args.verbose:
        console = logging.StreamHandler()
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
    
    if args.dataset_type == 'cleaneval':
        processor = CleanevalProcessor(output_dir, args.dataset_name)
        try:
            print '[CREATE BACKUPS]'
            processor.create_backups()
            print '[GENERATING META DATA]'
            processor.generate_meta_data()
            print '[PREPROCESSING]'
            processor.preprocess()
        except MetaGeneratorError as e:
            print 'META DATA RELATED ERROR:'
            print e
            sys.exit(-1)
        except PreprocessingError as e:
            print 'PREPROCESSING ERROR:'
            print e
            sys.exit(-1)
    elif args.dataset_type == 'google-news':
        processor = GooglenewsProcessor()
        #TODO
        
    print '[DONE]'
    
    
if __name__ == '__main__':
    main()


