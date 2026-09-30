# Travel Booking System - DevOps Project

A simple Flask travel booking website with the original travel services and booking functionality, extended with a lightweight DevOps lifecycle.

## Functional scope
- Destinations/search
- Flight and hotel services
- Package deals
- User registration/login
- Booking, update and cancellation
- Admin management

## DevOps scope
- Git/GitHub source control
- Jenkins CI/CD
- Pytest automated testing
- Docker containerization
- Kubernetes deployment
- RollingUpdate deployment strategy
- Deployment automation through Jenkins
- Prometheus + Grafana monitoring
- Kubernetes/application logs
- Trivy security scanning
- Project documentation

## Local setup
```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```
Open http://127.0.0.1:5000

## Docker
```powershell
docker compose up --build
```

## Minikube
```powershell
minikube start
minikube docker-env | Invoke-Expression
docker build -t travel-booking-system:latest .
kubectl apply -f k8s/
kubectl -n travel-booking rollout status deployment/travel-booking
minikube service travel-booking -n travel-booking
```

## Monitoring
```powershell
kubectl apply -f k8s/prometheus-config.yaml
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml
minikube service grafana -n travel-booking
```

## Logging
```powershell
kubectl -n travel-booking get pods
kubectl -n travel-booking logs <pod-name>
```

## Security
```powershell
trivy image --severity HIGH,CRITICAL --ignore-unfixed travel-booking-system:latest
```
