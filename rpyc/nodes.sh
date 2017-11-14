python reset.py 10001 10002 10003

python rpyc_server.py 10001 &
FIRST=$!

echo $FIRST

python rpyc_server.py 10002 &
SECOND=$!

echo $SECOND

python rpyc_server.py 10003 &
THIRD=$!

echo $THIRD

python rpyc_client.py 10002 10001
python rpyc_client.py 10001 10003

kill $FIRST
kill $SECOND
kill $THIRD
