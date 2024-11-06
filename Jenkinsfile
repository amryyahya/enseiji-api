pipeline {
    agent any
    environment {
        COMPOSE_PROJECT_NAME = 'expense_tracker'  
    }
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
        
        stage('Run Tests') {
            steps {
                // script {
                //     echo 'testing' 
                // }
                echo 'testing'
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
