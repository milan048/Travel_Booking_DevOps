pipeline {
    agent any

    environment {
        IMAGE = 'travel-booking-system:latest'
        NAMESPACE = 'travel-booking'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Automated Tests') {
            steps {
                bat 'docker run --rm -v "%WORKSPACE%:/app" -w /app -e PYTHONPATH=/app python:3.12-slim sh -c "pip install --no-cache-dir -r requirements.txt && pytest"'
            }
        }
        stage('Build Docker Image') {
            steps { bat 'docker build -t %IMAGE% .' }
        }
        stage('Security Scan') {
            steps { bat 'trivy image --severity HIGH,CRITICAL --ignore-unfixed %IMAGE%' }
        }
        stage('Deploy to Kubernetes') {
            steps {
                bat 'kubectl apply -f k8s/namespace.yaml'
                bat 'kubectl apply -f k8s/configmap.yaml'
                bat 'kubectl apply -f k8s/secret.yaml'
                bat 'kubectl apply -f k8s/deployment.yaml'
                bat 'kubectl apply -f k8s/service.yaml'
                bat 'kubectl -n %NAMESPACE% rollout status deployment/travel-booking --timeout=180s'
            }
        }
        stage('Monitoring') {
            steps {
                bat 'kubectl -n %NAMESPACE% get pods'
                bat 'kubectl -n %NAMESPACE% get svc'
            }
        }
    }
}
