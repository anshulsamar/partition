python rpyc_server.py 10001 &
FIRST=$!

echo $FIRST

python rpyc_server.py 10002 &
SECOND=$!

echo $SECOND

python rpyc_client.py 10002 10001

kill $FIRST
kill $SECOND
