# 🚀 3-Tier Flask + MySQL on AWS EKS | End-to-End DevOps Project

---

## 📌 Overview

A complete DevOps pipeline: **GitHub → Jenkins → Docker → DockerHub → AWS EKS (Kubernetes)**. The app is a Flask web service backed by MySQL with persistent storage (EBS), deployed via CI/CD.

---

## 🏗️ Architecture

```
Developer → GitHub → Jenkins → DockerHub → AWS EKS → Users
                               ↓
                         Kubernetes Cluster
                      ┌───────────────┬───────────────┐
                      ▼                               ▼
                Flask Pods (Deployment)        MySQL Pod (Deployment)
                      │                               │
                      ▼                               ▼
            Service (LoadBalancer)            PVC → EBS Volume
```

---

## 🧰 Tech Stack

* AWS EC2, EKS, EBS
* Docker, DockerHub
* Kubernetes
* Jenkins
* Git & GitHub
* Flask (Python), MySQL

---

# 🏁 STEP 1: Local Setup

```bash
git clone https://github.com/Nitin9606/3-tier-flask-with-mysql.git
cd 3-tier-flask-with-mysql

docker-compose up --build
# http://localhost:8081
```

---

# ☁️ STEP 2: EC2 (Jenkins Server)

* Ubuntu 22.04, ports: 22, 8080

```bash
ssh -i key.pem ubuntu@<EC2_IP>
```

---

# ⚙️ STEP 3: Install Docker & Git

```bash
sudo apt update
sudo apt install -y docker.io git unzip
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

---

# ⚙️ STEP 4: Install Jenkins

```bash
sudo apt install -y openjdk-11-jdk
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update && sudo apt install -y jenkins
sudo systemctl enable --now jenkins
# http://<EC2_IP>:8080
```

---

# 🔐 STEP 5: Jenkins Setup

* Plugins: Git, Docker Pipeline, Kubernetes CLI
* Credentials IDs:

  * `github-creds`
  * `dockerhub-creds`
  * `aws-creds`

---

# ☸️ STEP 6: Install AWS CLI, eksctl, kubectl

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip && sudo ./aws/install
aws configure

# eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/
```

---

# ☁️ STEP 7: Create EKS Cluster

```bash
eksctl create cluster --name my-cluster --region ap-south-1
aws eks --region ap-south-1 update-kubeconfig --name my-cluster
kubectl get nodes
```

---

# 📦 STEP 8: Namespace (optional)

```bash
kubectl create ns three-tier-app
kubectl config set-context --current --namespace=three-tier-app
```

---

# 🔐 STEP 9: Kubernetes Secret

```bash
kubectl create secret generic db-password-secret \
  --from-literal=db_password=root
```

---

# 🗄️ STEP 10: MySQL (Kubernetes - EBS)

## mysql-storage.yaml

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: mysql-sc
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: mysql-sc
  resources:
    requests:
      storage: 2Gi
```

## mysql-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  strategy: { type: Recreate }
  selector:
    matchLabels: { app: mysql }
  template:
    metadata:
      labels: { app: mysql }
    spec:
      containers:
      - name: mysql
        image: mysql:8
        ports:
        - containerPort: 3306
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-password-secret
              key: db_password
        - name: MYSQL_DATABASE
          value: devops_app
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: mysql-pvc
```

## mysql-service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
spec:
  clusterIP: None
  selector: { app: mysql }
  ports:
  - port: 3306
    targetPort: 3306
```

Apply:

```bash
kubectl apply -f k8s/mysql-storage.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/mysql-service.yaml
```

---

# 🚀 STEP 11: Flask App (Kubernetes)

## deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-deployment
spec:
  replicas: 2
  selector:
    matchLabels: { app: flask }
  template:
    metadata:
      labels: { app: flask }
    spec:
      containers:
      - name: flask
        image: nitinbijlwan/myapp-flaskapp:latest
        ports:
        - containerPort: 5000
        env:
        - name: DB_HOST
          value: mysql-service
        - name: DB_USER
          value: root
        - name: DB_NAME
          value: devops_app
        - name: DB_PASSWORD_FILE
          value: /run/secrets/db_password
        volumeMounts:
        - name: db-secret
          mountPath: /run/secrets
          readOnly: true
      volumes:
      - name: db-secret
        secret:
          secretName: db-password-secret
```

## service.yaml (LoadBalancer)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  type: LoadBalancer
  selector: { app: flask }
  ports:
  - port: 80
    targetPort: 5000
```

Apply:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

---

# 🌐 STEP 12: Access

```bash
kubectl get svc flask-service
# http://<EXTERNAL-IP>
```

---

# 🔄 STEP 13: Jenkins Pipeline (Jenkinsfile)

```groovy
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
```

Webhook:

```
http://<EC2_IP>:8080/github-webhook/
```

---

# 🔍 STEP 14: Verification

```bash
kubectl get pods
kubectl get svc
kubectl get pvc
kubectl logs <pod>
```

---

# 🛠️ Troubleshooting

* ImagePullBackOff → wrong image/tag or login
* CrashLoopBackOff → check env & logs
* MySQL not connecting → DB_HOST=mysql-service
* Jenkins Docker permission:

```bash
sudo usermod -aG docker jenkins && sudo systemctl restart jenkins
```

* EKS auth:

```bash
aws eks update-kubeconfig --name my-cluster
```

---

# 🧹 Cleanup

```bash
eksctl delete cluster --name my-cluster --region ap-south-1
docker system prune -a
```

---

# 🧠 DevOps Concepts

* Docker → portability
* Kubernetes → orchestration
* Jenkins → automation
* EKS → managed K8s
* CI/CD → continuous delivery

---

# 👨‍💻 Author

Nitin Bijlwan

---

# ⭐ Star the repo if helpful
