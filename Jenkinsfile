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
            steps {        
                 bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Microsoft\\WinGet\\Links\\trivy.exe" image --severity HIGH,CRITICAL --ignore-unfixed travel-booking-system:latest'
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" apply -f k8s\\namespace.yaml'
                bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" apply -f k8s\\configmap.yaml'
                bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" apply -f k8s\\secret.yaml'
                bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" apply -f k8s\\deployment.yaml'
                bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" apply -f k8s\\service.yaml'
            }
        }
        stage('Monitoring') {
            steps {
                 bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" -n %NAMESPACE% get pods -o wide'
                 bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" -n %NAMESPACE% get svc'
                 bat '"C:\\Users\\Milan Chauhan\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe" -n %NAMESPACE% get deployments'
            }
        }
    }
}
