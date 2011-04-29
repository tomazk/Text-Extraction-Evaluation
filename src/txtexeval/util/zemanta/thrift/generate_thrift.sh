echo "generating python source ..." 
thrift  -r -v -o .. --gen py:utf8strings ceservice.thrift 
echo "renaming gen-py into thriftgen"
mv ../gen-py ../thriftgen
echo "done"