'''
Script for generating meta data files and preprocessing datasets.

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
import argparse
import chardet
from BeautifulSoup import BeautifulSoup

from txtexeval.util import check_local_path, get_local_path

# module logger
logger = logging.getLogger()

# exceptions

class MetaGeneratorError(Exception):
    pass

class PreprocessingError(Exception):
    pass

class SkipTrigger(ValueError):
    pass

# private helpers
    
def _verify_args(args):
    # verify arguments provoded by argparse and
    # return the path to the output directory
    
    # printing arguments
    print 'dataset type: %s' % args.dataset_type
    print 'dataset name: %s' % args.dataset_name
    
    #validate dataset name
    if not check_local_path(args.dataset_name):
        print 'error: this dataset does not exist'
        sys.exit(-1)
    
    # validate path argument
    if args.path and not os.path.exists(args.path):
        print 'error: path does not exist'
        sys.exit(-1)
        
    output_dir = args.path or get_local_path(args.dataset_name)
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

def _get_charset(html_string, raw_filename):
    # based on a string that represents the html document
    # get the charset from the meta http-equiv tag e.g.:
    # <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    # or html5 <meta charset="UTF-8" />
    # return None if no such tag was found
    # raw_filename is used only for logging
    charset = None
    
    soup = BeautifulSoup(html_string)
    r_ct = re.compile('[C|c]ontent-[T|t]ype|CONTENT-TYPE')
    r_cont = re.compile('\s*text\s*/\s*html\s*;\s*charset\s*=\s*(?P<charset>[a-zA-Z0-9_-]+)')
    
    for tag in soup.findAll('meta'):
        
        if tag.has_key('http-equiv') and tag.has_key('content') and r_ct.match(tag['content']):
            content = tag['content'].lower()
            match = r_cont(content)
            if match:
                charset = match.group('charset')
                logger.debug('charset %s found via meta http-equiv in %s', charset, raw_filename)
            else:
                logger.warn('meta http-equiv exists but it does not match the content regex in %s: %s', raw_filename, str(tag))
        
        elif tag.has_key('http-equiv') and not tag.has_key('content'):
            logger.warn('no content attribute in meta http-equiv tag in %s: %s', raw_filename, str(tag))
        
        elif tag.has_key('charset'):
            charset = tag['charset']
            logger.info('charset %s found via meta charset (html5 style) in %s', charset, raw_filename)
        
    if not charset:
        logger.debug('no meta tag with charset definition in %s', raw_filename)
            
    return charset

def _get_safe_encoding_name(encoding):
    try:
        codec = codecs.lookup(encoding)
    except LookupError:
        raise MetaGeneratorError('no safe encoding name is found for %s' % encoding)
    else:
        return codec.name
    
def _skip_file(regex, raw_filename):
    # valiadate raw filenames
    if not regex.match(raw_filename):
        logger.debug('skipping file %s', raw_filename)
        raise SkipTrigger

# decorators

def itarate_raw_filename(method):
    def wrap(self):
        for raw_filename in self._raw_filenames():
            try:
                method(self, raw_filename)
            except SkipTrigger:
                continue
    return wrap

def dump_meta_data(method):
    def wrap(self,*args,**kwargs):
        method(self,*args,**kwargs)
        self._serialize_meta_data()
    return wrap
    
# dataset specific processor classes

class BaseProcessor(object):
    
    def __init__(self, output_dir, dataset_name):   
        self._dataset_dir = get_local_path(dataset_name)
        self._output_dir = output_dir
        self.meta_data_list = [] # list to be serialized
    
    def _raw_filenames(self):       
        return os.listdir(os.path.join(self._dataset_dir, 'raw')) 
    
    def _clean_filenames(self):
        return os.listdir(os.path.join(self._dataset_dir, 'clean'))
    
    def _serialize_meta_data(self):
        with open(os.path.join(self._output_dir, 'meta.yaml'), 'w') as meta_file:
            meta_string = yaml.dump(self.meta_data_list, default_flow_style=False) 
            meta_file.write(meta_string)
    
    
class GooglenewsProcessor(BaseProcessor):
    
    re_TAIL = re.compile(r'(?P<id>.+)\.html$')
    
    @dump_meta_data    
    @itarate_raw_filename
    def generate_meta_data(self, raw_filename):
        _skip_file(self.re_TAIL, raw_filename)
        
        with open(os.path.join(self._dataset_dir, 'raw', raw_filename), 'r' ) as f:
            # check for cleaned file counterpart
            if not os.path.exists(os.path.join(self._dataset_dir, 'clean', raw_filename )):
                raise MetaGeneratorError('No existing clean file counterpart for %s' % raw_filename)
            
            html_string = f.read()
            
            charset = _get_charset(html_string, raw_filename)
            confidence = None
            # if no charset is retrieved with document parsing
            # use chardet library to detect encoding
            if charset:
                raw_encoding = charset
            else:
                det = chardet.detect(html_string)
                raw_encoding = det['encoding']
                confidence =  det['confidence']
                logger.debug('detected encoding %s in %s with confidence %f', raw_encoding, raw_filename, confidence)
                
            safe_raw_encoding = _get_safe_encoding_name(raw_encoding)
            
            self.meta_data_list.append(dict(
                id = self.re_TAIL.match(raw_filename).group('id'),
                url = None,
                raw_encoding = safe_raw_encoding,
                clean_encoding = safe_raw_encoding, # TODO: must verify if this is allways true
                raw = raw_filename, 
                clean = raw_filename,
                meta = {'encoding_confidence': confidence}
            ))
                    
              
class CleanevalProcessor(BaseProcessor):
    
    re_BACK = re.compile(r'^(?P<id>\d+)\.html\.backup$')
    re_NEW = re.compile(r'^\d+\.html$')
    
    @itarate_raw_filename
    def create_backups(self, raw_filename):
        # rename every unprocessed [number].html to [number].html.backup 
        
        raw_filename_path = os.path.join(self._dataset_dir, 'raw', raw_filename)
        backup_path = raw_filename_path + '.backup'
        logger.info('renaming %s to %s', raw_filename, raw_filename + '.backup')
        os.rename(raw_filename_path, backup_path)
    
    @dump_meta_data
    @itarate_raw_filename
    def generate_meta_data(self, raw_filename):
        _skip_file(self.re_BACK, raw_filename)
        with open(os.path.join(self._dataset_dir, 'raw', raw_filename), 'r' ) as f:
            html_string = f.read()
            
            # check for an existing clean file counterpart
            clean_filename = raw_filename.replace('.html.backup', '') + '-cleaned.txt'
            if not os.path.exists(os.path.join(self._dataset_dir, 'clean', clean_filename )):
                raise MetaGeneratorError('No existing clean file counterpart for %s' % raw_filename)
            
            # get meta data from <text ...> tag
            soup = BeautifulSoup(html_string)
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
                safe_encoding = _get_safe_encoding_name(encoding)
            except MetaGeneratorError:
                det = chardet.detect(html_string)
                safe_encoding = _get_safe_encoding_name(det['encoding'])
                logger.info('detected encoding %s in %s with confidence %f', safe_encoding, raw_filename, det['confidence'] )
    
            logger.debug('generating meta data for %s', raw_filename)
            self.meta_data_list.append(dict(
                id = self.re_BACK.match(raw_filename).group('id'),
                url = None,
                raw_encoding = safe_encoding,
                # acording to anotation guidelines of cleaneval 
                # all cleaned text files are utf-8 encoded
                clean_encoding = 'utf-8',
                # we'll be generating [number].html in the preprocessing phase
                raw = raw_filename.replace('.backup', 'iii'), 
                clean = clean_filename,
                meta = cleaneval_specific
            ))
   
    @itarate_raw_filename
    def preprocess(self, raw_filename):
        # remove all <text> tags
        # add missing <html><body> tags where needed
                
        _skip_file(self.re_BACK, raw_filename)
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

def parse_args():               
    # sys argument parsing using argparse
    parser = argparse.ArgumentParser(description = 'Tool for generating meta data files and cleanup preprocessing regarding datasets')
    parser.add_argument('dataset_type', choices = ('cleaneval','gnews'), help = 'dataset type e.g. cleaneval' )
    parser.add_argument('dataset_name', help = 'name of the dataset')
    parser.add_argument('-p','--path', help = 'path to the meta data output file and .log file (uses the default path if not provided)')
    parser.add_argument('-v','--verbose', action = 'store_true', help = 'print log to console')
    return parser.parse_args()
                
def main():
    args = parse_args()
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
        console.setLevel(logging.DEBUG)
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
            
    elif args.dataset_type == 'gnews':
        processor = GooglenewsProcessor(output_dir, args.dataset_name)
        try:
            print '[GENERATING META DATA]'
            processor.generate_meta_data()
        
        except MetaGeneratorError as e:
            print 'META DATA RELATED ERROR:'
            print e
            sys.exit(-1)
        except PreprocessingError as e:
            print 'PREPROCESSING ERROR:'
            print e
            sys.exit(-1)
            
    print '[DONE]'
    
    
if __name__ == '__main__':
    main()