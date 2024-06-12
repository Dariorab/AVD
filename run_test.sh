#!/bin/bash
#qdtrack_ training.xml
# export ROUTES=/workspace/team_code/route_controlling.xml
export ROUTE_NAME=route_4
export ROUTES=/workspace/team_code/routes/${ROUTE_NAME}_avddiem.xml #TO EDIT
export REPETITIONS=1
export DEBUG_CHALLENGE=1
export TEAM_AGENT=/workspace/team_code/carla_behaviour_agent/basic_autonomous_agent.py #TO EDIT
export TEAM_CONFIG=/workspace/team_code/carla_behaviour_agent/config_agent_basic.json #TO EDIT
export CHALLENGE_TRACK_CODENAME=SENSORS
export CARLA_HOST=0.0.0.0 #TO EDIT WITH REMOTE HOST (...)
export CARLA_PORT=6006
export CARLA_TRAFFIC_MANAGER_PORT=8806

timestamp=$(date +'%Y%m%d_%H%M')

export CHECKPOINT_ENDPOINT=/workspace/team_code/results/${timestamp}_${ROUTE_NAME}_simulation_results.json
export DEBUG_CHECKPOINT_ENDPOINT=/workspace/team_code/results/${timestamp}_${ROUTE_NAME}_live_results.txt
export RESUME=true
export TIMEOUT=60

python3 ${LEADERBOARD_ROOT}/leaderboard/leaderboard_evaluator.py \
--routes=${ROUTES} \
--routes-subset=${ROUTES_SUBSET} \
--repetitions=${REPETITIONS} \
--track=${CHALLENGE_TRACK_CODENAME} \
--checkpoint=${CHECKPOINT_ENDPOINT} \
--debug-checkpoint=${DEBUG_CHECKPOINT_ENDPOINT} \
--agent=${TEAM_AGENT} \
--agent-config=${TEAM_CONFIG} \
--debug=${DEBUG_CHALLENGE} \
--record=${RECORD_PATH} \
--resume=${RESUME} \
--host=${CARLA_HOST} \
--port=${CARLA_PORT} \
--timeout=${TIMEOUT} \
--traffic-manager-port=${CARLA_TRAFFIC_MANAGER_PORT} 
