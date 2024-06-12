## Project work AVD

### TO-DO:
- [ ] Modificare PID 
- [ ] Da inserire
- [ ] Da inserire


### command for Local execution
```bash
sudo docker container stop carla_leaderboard_server
```

1. ```bash
    sudo /home/darius22-04/Desktop/CARLA/carla_leaderboard/docker_run.sh
    ```

2. ```bash
    cd /home/darius22-04/Desktop/CARLA/client_carla
    python3 userCode/server_http.py
    ```
3. ```bash
    cd /home/darius22-04/Desktop/CARLA/client_carla
    sudo docker build --force-rm -t carla-client . &&
    sudo ./docker_run.sh
   ```

### Docker run Client

```bash
docker run --rm \
	-v $(pwd)/userCode/:/workspace/team_code/ \
	--network=host \
	--name carla-client-instance-${USER} \
	-p 8806:8806 \
	-p 9806:9806 \ # To edit
	-it carla-client \
	/bin/bash 
```

### Docker run Server Local

```bash
docker run --privileged --rm --gpus all --network=host --name carla_leaderboard_server -d carla_leaderboard /bin/bash ./CarlaUE4.sh -carla-port=6006 -RenderOffScreen
```