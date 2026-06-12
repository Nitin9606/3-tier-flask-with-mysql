pipeline {
  agent any
  environment {
    DOCKER_IMAGE = 'nitinbijlwan/myapp-flaskapp'
    TAG = "v1.${BUILD_NUMBER}"
    AWS_REGION = 'ap-south-1'
    EKS_CLUSTER = 'my-cluster'
  }
  stages {
    stage('Clone') {
      steps {
        git branch: 'main', url: 'https://github.com/Nitin9606/3-tier-flask-with-mysql.git', credentialsId: 'github-creds'
      }
    }
    stage('Build') {
      steps { sh 'docker build -t $DOCKER_IMAGE:$TAG .' }
    }
    stage('Login DockerHub') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
          sh 'echo $PASS | docker login -u $USER --password-stdin'
        }
      }
    }
    stage('Push') {
      steps {
        sh 'docker push $DOCKER_IMAGE:$TAG'
        sh 'docker tag $DOCKER_IMAGE:$TAG $DOCKER_IMAGE:latest'
        sh 'docker push $DOCKER_IMAGE:latest'
      }
    }
    stage('Configure EKS') {
      steps {
        withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-creds']]) {
          sh 'aws eks --region $AWS_REGION update-kubeconfig --name $EKS_CLUSTER'
        }
      }
    }
    stage('Deploy') {
      steps {
        sh '''
        sed -i "s|image: .*|image: $DOCKER_IMAGE:$TAG|g" k8s/deployment.yaml
        kubectl apply -f k8s/mysql-storage.yaml
        kubectl apply -f k8s/mysql-deployment.yaml
        kubectl apply -f k8s/mysql-service.yaml
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        '''
      }
    }
  }
}
