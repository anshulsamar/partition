#python reset_test.py 20001 20002

python setup.py test_vertices.txt test_edges.txt

python rpyc_server.py 20000 & 
FIRST=$!

echo $FIRST

#python rpyc_server.py 20002 &
#SECOND=$!

#echo $SECOND


#python rpyc_server.py 20003 &
#THIRD=$!

#echo $THIRD

python rpyc_connection.py 20001 20000 &
SECOND=$!
echo $SECOND

python rpyc_connection.py 20002 20001 20000 &
THIRD=$!
echo $THIRD

kill $FIRST
kill $SECOND
kill $THIRD
