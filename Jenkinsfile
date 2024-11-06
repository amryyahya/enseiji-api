pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                script {
                    sh 'docker compose -f docker-compose.yaml build'
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    sh 'docker exec -it expense-tracker-api env PYTHONPATH=/app pytest' 
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    sh 'docker compose -f docker-compose.yaml up -d'
                }
            }
        }
    }
    post {
        always {
            script {
                sh 'docker compose -f docker-compose.yaml down'
            }
        }
        failure {
            echo 'Build failed.'
        }
        success {
            echo 'Build succeeded!'
        }
    }
}
