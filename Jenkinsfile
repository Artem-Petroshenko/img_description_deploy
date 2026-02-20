pipeline {
    agent { label 'pav1' }

    environment {        
        CR_REGISTRY_ID    = 'crpg1hg800n8hofip04v'
        CR_FOLDER_ID      = 'b1gp0ouuf2oaj9r2iubo'
                
        K8S_NAMESPACE     = 'petroshenko'
        K8S_CLUSTER_ID    = 'catl6i81g779o87dbfn4'
    }

    parameters {
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag')
        booleanParam(name: 'SKIP_BUILD', defaultValue: false, description: 'Skip build & push')
        booleanParam(name: 'DRY_RUN', defaultValue: false, description: 'Validate manifests only')
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Build & Push Images') {
			when { expression { !params.SKIP_BUILD } }
			steps {
				sh '''
					set -e
										
					export PATH="/home/ubuntu/yandex-cloud/bin:$PATH"
					export YC_CONFIG_DIR=/home/ubuntu/.yc					
					
					echo "==> Authenticate Docker with Yandex Container Registry"
					/home/ubuntu/yandex-cloud/bin/yc container registry configure-docker
					
					echo "==> Build Docker images"
					cd Infrastructure					
					docker build -t ml-core-service:latest -f ../ml-core-service/Dockerfile ../ml-core-service/									
					docker build -t tg-bot:latest -f ../tg-bot/Dockerfile ../tg-bot/
					
					echo "==> Tag images for Yandex CR"
					docker tag ml-core-service:latest cr.yandex/${CR_REGISTRY_ID}/ml-core-service:${IMAGE_TAG}
					docker tag tg-bot:latest cr.yandex/${CR_REGISTRY_ID}/tg-bot:${IMAGE_TAG}
					
					echo "==> Push images to Yandex CR"
					docker push cr.yandex/${CR_REGISTRY_ID}/ml-core-service:${IMAGE_TAG}
					docker push cr.yandex/${CR_REGISTRY_ID}/tg-bot:${IMAGE_TAG}
					
					echo "✅ Images pushed: ${IMAGE_TAG}"
				'''
			}
		}

        stage('Update manifests with image tag') {
            steps {
                sh '''
                    set -e
                    echo "==> Update k8s manifests with image tag: ${IMAGE_TAG}"
                    
                    sed -i "s|cr.yandex/<REG_ID>/ml-core-service:latest|cr.yandex/${CR_REGISTRY_ID}/ml-core-service:${IMAGE_TAG}|g" k8s/ml-core-service.yaml
                    sed -i "s|cr.yandex/<REG_ID>/tg-bot:latest|cr.yandex/${CR_REGISTRY_ID}/tg-bot:${IMAGE_TAG}|g" k8s/telegram-bot.yaml
                    
                    grep "image:" k8s/ml-core-service.yaml k8s/telegram-bot.yaml
                '''
            }
        }

        stage('Validate Kubernetes manifests') {
			steps {
				sh '''
					set -e
					echo "==> Validate manifests with kubectl"
					
					# Проверка синтаксиса и применимости манифестов
					kubectl apply -f k8s/ --dry-run=client -n ${K8S_NAMESPACE}
					
					echo "✅ Manifests validated successfully"
				'''
			}
		}

        stage('Deploy to Kubernetes') {
            when { expression { !params.DRY_RUN } }
            steps {
                sh '''
                    set -e
					echo "==> Clean up old deployments (avoid rolling update issues)"
					kubectl delete deployment --all -n ${K8S_NAMESPACE} 2>/dev/null || true
					kubectl delete pod --all -n ${K8S_NAMESPACE} 2>/dev/null || true
					sleep 5  
					
                    echo "==> Apply Kubernetes manifests"
                    kubectl apply -f k8s/namespace.yaml
                    kubectl apply -f k8s/postgres.yaml
                    kubectl apply -f k8s/redis.yaml
                    kubectl apply -f k8s/ml-core-service.yaml
                    kubectl apply -f k8s/telegram-bot.yaml
                    kubectl apply -f k8s/grafana.yaml
                    echo "✅ Manifests applied"
                '''
            }
        }

        stage('Wait for deployments') {
            when { expression { !params.DRY_RUN } }
            steps {
                sh '''
                    set -e
                    echo "==> Wait for deployments to be ready"
                    kubectl rollout status deployment/ml-core-service -n ${K8S_NAMESPACE} --timeout=300s
                    kubectl rollout status deployment/telegram-bot -n ${K8S_NAMESPACE} --timeout=120s
                    kubectl rollout status deployment/grafana -n ${K8S_NAMESPACE} --timeout=60s
                    echo "✅ All deployments ready"
                '''
            }
        }

        stage('Health Check') {
            when { expression { !params.DRY_RUN } }
            steps {
                script {
                    def nodeIp = sh(
                        script: "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"ExternalIP\")].address}'",
                        returnStdout: true
                    ).trim()
                    
                    if (nodeIp.isEmpty()) {
                        nodeIp = sh(
                            script: "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}'",
                            returnStdout: true
                        ).trim()
                    }
                    
                    echo "==> Health check on node: ${nodeIp}"
                    
                    sh """
                        set -e
                        echo "==> Check ML service health"
                        for i in \$(seq 1 10); do
                            if curl -sf --max-time 10 http://${nodeIp}:30100/api/health; then
                                echo "✅ ML service is healthy"
                                break
                            fi
                            echo "⏳ Waiting... attempt \$i"
                            sleep 5
                        done
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🎉 K8s deployment SUCCESS!"
            echo "📊 Grafana: http://<NODE_IP>:30101"
            echo "🔍 ML Health: http://<NODE_IP>:30100/api/health"
        }
        failure {
            echo "❌ K8s deployment FAILED"
            echo "🔎 Debug: kubectl get pods -n petroshenko"
        }
        cleanup {
            cleanWs()
        }
    }
}