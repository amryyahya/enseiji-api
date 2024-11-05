pipeline {
    agent {
        docker { 
            image 'docker:stable-dind' 
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
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
                    sh 'docker-compose -f docker-compose.yml build'
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
                    sh 'docker-compose -f docker-compose.yml up -d'
                }
            }
        }
    }
    post {
        always {
            script {
                sh 'docker-compose -f docker-compose.yml down'
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
