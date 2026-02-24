pipeline {
    agent { label 'pav1' }

    environment {
        PYTHONNOUSERSITE          = "1"
        SSH_KEY_PATH              = "/home/ubuntu/.ssh/id_rsa"
        ANSIBLE_HOST_KEY_CHECKING = "False"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Smoke test (local)') {
            steps {
                sh '''
                    set -e
					echo "==> Create external Docker volumes (if not exist)"
					
					docker volume create pixname_pgdata || true
					docker volume create pixname_grafana-storage || true
					docker volume create infrastructure_redis_data || true

                    echo "==> Local docker-compose build & smoke test"

                    cd Infrastructure
                    docker compose down -v || true
                    docker compose up -d --build

                    echo "==> Waiting for ML service"
                    sleep 20

                    echo "==> Curl /api/health"
                    curl -f http://localhost:8000/api/health
                '''
            }
        }

        stage('Terraform: provision infra') {
            steps {
                dir('openstack') {
                    sh '''
                        set -e
                        echo "==> Source OpenStack creds"
                        . /home/ubuntu/openrc-jenkins.sh

                        echo "==> Ensure keypair does not exist"
                        openstack keypair delete img_description || true

                        echo "==> Generate terraform.tfvars"
                        cat > terraform.tfvars <<EOF
auth_url      = "${OS_AUTH_URL}"
tenant_name   = "${OS_PROJECT_NAME}"
user_name     = "${OS_USERNAME}"
password      = "${OS_PASSWORD}"
region        = "${OS_REGION_NAME:-RegionOne}"

image_name    = "ununtu-22.04"
flavor_name   = "m1.medium"
network_name  = "sutdents-net"

public_ssh_key = "$(cat /home/ubuntu/.ssh/id_rsa.pub)"
EOF

                        echo "==> Terraform init"
                        terraform init -input=false

                        echo "==> Terraform apply"
                        terraform apply -auto-approve -input=false
                    '''
                }
            }
        }

        stage('Wait for VM SSH') {
            steps {
                script {
                    def vmIp = sh(
                        script: "cd openstack && terraform output -raw Petroshenko-terraform_ip",
                        returnStdout: true
                    ).trim()

                    echo "Waiting for SSH on ${vmIp}"

                    sh """
                        set -e
                        for i in \$(seq 1 30); do
                            echo "==> Checking SSH (${vmIp}) attempt \$i"
                            if nc -z -w 5 ${vmIp} 22; then
                                echo "==> SSH is UP!"
                                exit 0
                            fi
                            echo "==> SSH not ready, sleep 10s"
                            sleep 10
                        done
                        echo "ERROR: SSH did not start in time"
                        exit 1
                    """
                }
            }
        }

        stage('Ansible: deploy to img_description VM') {
            steps {
                script {
                    def vmIp = sh(
                        script: "cd openstack && terraform output -raw Petroshenko-terraform_ip",
                        returnStdout: true
                    ).trim()

                    echo "VM IP from Terraform: ${vmIp}"

                    sh """
                        set -e

                        # Clean old host key for this IP
                        mkdir -p ~/.ssh
                        ssh-keygen -R ${vmIp} || true

                        cd ansible

                        echo "==> Generate inventory.ini"
                        cat > inventory.ini <<EOF
[img_description]
${vmIp} ansible_user=ubuntu ansible_ssh_private_key_file=${SSH_KEY_PATH}
EOF

                        echo "==> Run ansible-playbook"
                        ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory.ini playbook.yml
                    """
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline SUCCESS: img_description_deploy build → infra → deploy completed."
        }
        failure {
            echo "❌ Pipeline FAILED. Check logs for details."
        }
    }
}
