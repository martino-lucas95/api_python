pipeline{
    agent any
    stages{
        stage('Build'){
            steps{
                sh 'python3 --version'
                sh 'pip3 install -r requirements.txt'
                sh 'python3 main.py'
            }
        }
    }
}