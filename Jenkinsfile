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
                    sh 'docker compose build'
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    sh 'docker compose up -d'
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
    }
    post {
        always {
            script {
                sh 'docker compose down'
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
