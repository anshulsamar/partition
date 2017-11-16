python reset_test.py 20001 20002

python rpyc_server.py 20001 &
FIRST=$!

echo $FIRST

python rpyc_server.py 20002 &
SECOND=$!

echo $SECOND

python rpyc_connection.py 10002 10001
python rpyc_connection.py 10001 10003

kill $FIRST
kill $SECOND
