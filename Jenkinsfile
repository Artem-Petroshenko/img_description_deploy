pipeline {
  agent none

  options {
    skipDefaultCheckout(true)
    timestamps()
  }

  stages {
    stage('Checkout (on agent)') {
      agent { label 'pixname-node' }   // <-- поменяй на label твоей ноды
      steps {
        checkout scm
        sh '''
          set -eux
          whoami
          hostname
          git --version
          docker --version
          docker-compose --version || true
          docker compose version || true
        '''
      }
    }

    stage('Build images') {
      agent { label 'pixname-node' }
      steps {
        sh '''
          set -eux
          cd Infrastructure
          # Compose v2 обычно: docker compose, но у тебя есть docker-compose v2.23.1
          docker-compose build
        '''
      }
    }

    stage('Deploy (restart)') {
      agent { label 'pixname-node' }
      steps {
        sh '''
          set -eux
          cd Infrastructure

          # аккуратный рестарт
          docker-compose down || true
          docker-compose up -d

          docker ps
        '''
      }
    }

    stage('Healthcheck') {
      agent { label 'pixname-node' }
      steps {
        sh '''
          set -eux
          cd Infrastructure

          # Пример проверки API
          curl -sf http://localhost:8000/api/health || true
          curl -sf http://localhost:8000/api/docs >/dev/null || true

          docker-compose ps
        '''
      }
    }
  }

  post {
    failure {
      echo 'Pipeline failed!'
    }
  }
}
