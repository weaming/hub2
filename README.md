# Hub2

Subscribe topics on https://hub.drink.cafe

Bot: [hub2](https://t.me/hub2_bot)

## Run in docker

```
docker run -it --rm -e API_TOKEN=<TOKEN> -v $HOME/docker/hub2/tmp:/tmp --name hub2 weaming/hub2
docker run -d -e API_TOKEN=<TOKEN> -v $HOME/docker/hub2/tmp:/tmp --name hub2 weaming/hub2
```

## Develop

1. Setup proxy using environment `https_proxy`
2. Install python3.7.4 using `pyenv install 3.7.4`
3. Setup virtualenv
4. Export `API_TOKEN` of telegram bot
5. `python main.py`
