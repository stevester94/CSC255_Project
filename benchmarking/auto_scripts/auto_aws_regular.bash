SSH_USERNAME=ubuntu
SERVER_SSH_IP=aws_singapore.ssmackey.com
SERVER_TEST_IP=aws_singapore.ssmackey.com
CLIENT_SSH_IP=aws_oregon.ssmackey.com
PROTOCOL=tcp
PORT=9001
DURATION=30
METRICS_INTERVAL=1
PATH_TO_SSH_CERT=/home/steven/KEYS/aws_ssmackey_ssh_key.pem
RESULTS_FILE_PREFIX=regular

./run_benchmark.bash $SSH_USERNAME $SERVER_SSH_IP $SERVER_TEST_IP $CLIENT_SSH_IP $PROTOCOL $PORT $DURATION $METRICS_INTERVAL $PATH_TO_SSH_CERT $RESULTS_FILE_PREFIX 
