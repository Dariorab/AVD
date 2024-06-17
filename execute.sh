#/bin/bash
export CLIENT_DIR=/home/darius22-04/Desktop/CARLA/client_carla

visualizer="cd ${CLIENT_DIR} && python3 userCode/server_http.py; exec bash"
server="sudo /home/darius22-04/Desktop/CARLA/carla_leaderboard/docker_run.sh &&
        cd .. && sudo ./docker_run.sh; exec bash"

gnome-terminal --tab -- sh -c "$visualizer"
gnome-terminal -- sh -c "$server"



