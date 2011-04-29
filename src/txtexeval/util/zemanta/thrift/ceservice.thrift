
// Command line to produce py-gen directory:
//  ~/prefix/bin/thrift -r --gen py:utf8strings ceservice.thrift

enum ExceptionCode {
	FORCED_FAILED = 1,
	PARSING_FAILED = 2,
	FLATTENING_FAILED = 3,
	CLASSIFICATION_FAILED = 4,
}


exception TAppException {
	1: ExceptionCode code,
	2: string msg,
 	3: string backtrace,
}

struct extract_RET
{
	1:bool success,
	2:string body,
}

service ExtractorService
{
	string ping(1: string param)
		throws (1:TAppException e),


	extract_RET extract(
		1:string url, 
		2:string title, 
		3:binary htmldata, 
		4:string encoding,
		)
		throws (1:TAppException e),
}

