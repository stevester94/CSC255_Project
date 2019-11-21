if [ "$#" -ne 10 ]; then
    echo "Usage: <ssh username> <server ssh ip> <server test ip> <client ssh ip> <protocol> <port> <test duration> <metrics interval> <path to ssh cert> <results file prefix>"
    echo "    Note: username and ssh certificate must be the same for both client and server machines"
    echo "    Note: the results file prefix arg can be anything, it just prefixes the json result files with whatever you give it"
    exit
fi

echo $#

SSH_USERNAME=$1
SERVER_SSH_IP=$2
SERVER_TEST_IP=$3
CLIENT_SSH_IP=$4
PROTOCOL=$5
PORT=$6
DURATION=$7
INTERVAL=$8
PATH_TO_CERT=$9
RESULTS_PREFIX=${10}

BENCHMARK_ROOT_DIR="/home/ubuntu/CSC255_Project/benchmarking/"
#BENCHMARK_ROOT_DIR="/home/steven/School/CSC255/CSC255_Project/benchmarking/"

SERVER_RESULTS_NAME=$RESULTS_PREFIX"_server_results.json"
CLIENT_RESULTS_NAME=$RESULTS_PREFIX"_client_results.json"
SERVER_RESULTS_OUT_PATH="~/$SERVER_RESULTS_NAME"
CLIENT_RESULTS_OUT_PATH="~/$CLIENT_RESULTS_NAME"

BINARY_NAME="metrics.py"


SERVER_COMMAND="$BENCHMARK_ROOT_DIR$BINARY_NAME server $PROTOCOL $SERVER_TEST_IP $PORT $DURATION $INTERVAL $SERVER_RESULTS_OUT_PATH"
CLIENT_COMMAND="$BENCHMARK_ROOT_DIR$BINARY_NAME client $PROTOCOL $SERVER_TEST_IP $PORT $DURATION $INTERVAL $CLIENT_RESULTS_OUT_PATH"

echo "clearing previous results"
ssh -i $PATH_TO_CERT $SSH_USERNAME@$SERVER_SSH_IP rm $SERVER_RESULTS_OUT_PATH
ssh -i $PATH_TO_CERT $SSH_USERNAME@$CLIENT_SSH_IP rm $CLIENT_RESULTS_OUT_PATH 

echo "Server command to be executed: " $SERVER_COMMAND
echo "Client command to be executed: " $CLIENT_COMMAND

echo "Server ssh command: " ssh -i $PATH_TO_CERT $SSH_USERNAME@$SERVER_SSH_IP $SERVER_COMMAND
echo "Client ssh command: " ssh -i $PATH_TO_CERT $SSH_USERNAME@$CLIENT_SSH_IP $CLIENT_COMMAND

echo "starting server"
ssh -i $PATH_TO_CERT $SSH_USERNAME@$SERVER_SSH_IP $SERVER_COMMAND > /dev/null &
sleep 1 # Wait a bit for the server to actually come up
echo "starting client"
ssh -i $PATH_TO_CERT $SSH_USERNAME@$CLIENT_SSH_IP $CLIENT_COMMAND > /dev/null &

echo "Sleeping for $DURATION+10 seconds"
# Sleep while the tests run in the background
sleep 10
sleep $DURATION

echo "Done, fetching the results"
scp -i $PATH_TO_CERT $SSH_USERNAME@$SERVER_SSH_IP:$SERVER_RESULTS_OUT_PATH .
scp -i $PATH_TO_CERT $SSH_USERNAME@$CLIENT_SSH_IP:$CLIENT_RESULTS_OUT_PATH .

./results_processor.py  $SERVER_RESULTS_NAME &
./results_processor.py  $CLIENT_RESULTS_NAME &
