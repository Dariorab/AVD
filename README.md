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
    python3 server_http.py
    ```
3. ```bash
    cd /home/darius22-04/Desktop/CARLA/client_carla/
    sudo docker build --force-rm -t carla-client . &&
    sudo ./docker_run.sh
   ```
