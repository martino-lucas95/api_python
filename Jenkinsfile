pipeline{
    agent any
    stages{
        stage('Build'){
            steps{
                sh 'python3 --version'
                sh 'pip3 install flask flasgger'
                sh 'python3 main.py'
            }
        }
    }
}