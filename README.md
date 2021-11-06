# Prediction Api

```bash
tree .

├── Dockerfile
├── README.md
├── deployment.yaml
├── requirements.pip
├── run_me.py
├── src
│   ├── __init__.py
│   ├── adapters
│   │   ├── __init__.py
│   │   ├── mongo_connector.py
│   │   └── redis_connector.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── validators.py
│   ├── app.py
│   ├── common
│   │   ├── __init__.py
│   │   └── utils.py
│   ├── domain
│   │   ├── __init__.py
│   │   └── models.py
│   ├── scripts
│   │   └── __init__.py
│   └── service_layer
│       └── __init__.py
└── tests
    ├── __init__.py
    ├── common
    │   └── __init__.py
    ├── integration
    │   ├── __init__.py
    │   └── handlers_test.py
    └── unit
        ├── __init__.py
        └── handlers_test.py


```
## Installation

- Kubernetes
```bash
docker build -f Dockerfile  -t prediction-api:latest .
kubectl apply -f deployment.yaml
```
- Docker
```bash
docker build -f Dockerfile  -t prediction-api:latest .
docker run -p 8586:8585 prediction-api
```
- Manual
```bash
pip install git+ssh://git@git.tapsell.ir:3031/brain/mlaas.git
pip install -r requirements.pip
python src/app.py --port 8585 --config ./configs/prediction-api-local.yml 
```


## Running Tests
```bash
python run_me.py typecheck 
python run_me.py lint
python run_me.py test --suite unit
python run_me.py test --suite integration
```