import groovy.io.FileType
def schema_registry
def templates
def schemas_dir
def bootstrap_servers
def git_url

pipeline {
  agent none
  environment {
	  GIT_CREDS = credentials('github_creds_for_jenkins')
	  SSH_CREDS = credentials('ssh_creds_e960438adm')
    }
  options { disableConcurrentBuilds() }

  stages {

		stage('extract from previous stage') {
			agent { label 'linux' }
			when { environment name: 'BRANCH_NAME', value: 'FAIT' }
			steps{
				echo "branch : ${env.BRANCH_NAME}"
				sh 'cp /var/lib/jenkins/ikep_transports.py .'

				script {
					git_url = "${env.GIT_URL}".drop(8)
					echo "url: ${git_url}"
					templates = new File("${env.WORKSPACE}/templates.1").listFiles()
					echo "templates: ${templates}"
					schemas_dir = "\\\"${env.WORKSPACE}/schemas\\\""

					if ((env.BRANCH_NAME) == 'FAIT') {
						schema_registry = "\\\"https://kfkie0z313.linux.eden:8081\\\""
						bootstrap_servers = 'kfkie0z231.linux.eden:9094'
						}
					else if ((env.BRANCH_NAME) == 'ERGODEV') {
						schema_registry = "\\\"https://kfkie0y311.linux.eden:8081\\\""
						bootstrap_servers = 'kfkie0y231.linux.eden:9094'
						}

				echo "sr_url: ${schema_registry}"
				echo "schemas_dir: ${schemas_dir}"

				templates.each {
				sh """
				python -c "import ikep_transports; ikep_transports.readSchema(${schema_registry}, ${schemas_dir})" ${it.path} ${schema_registry} ${bootstrap_servers} ${schemas_dir}
				"""
				}
			}

				echo "pushing the extracted schemas to the branch: ${env.BRANCH_NAME}"
				sh "git remote rm origin"
				sh "git add ${env.WORKSPACE}/schemas"
					sh "git remote add origin https://${GIT_CREDS_USR}:${GIT_CREDS_PSW}@${git_url}"                     
				sh "git commit -a -m 'added schema files' | true" 
				sh "git push origin HEAD:${env.BRANCH_NAME}"
				
			}
		}

		stage('transport to next stage') {
			agent { label 'linux' }
			when { environment name: 'BRANCH_NAME', value: "${env.TAG_NAME}" } 	
			steps{
				echo "TAG: ${env.TAG_NAME}"
				sh 'cp /var/lib/jenkins/ikep_transports.py .'

				script {
					templates = new File("${env.WORKSPACE}/templates.1").listFiles()
					echo "templates: ${templates}"
					schemas_dir = "${env.WORKSPACE}/schemas"

					if ((env.TAG_NAME).startsWith('FAIT-v')) {
						schema_registry = "https://kfkie0z313.linux.eden:8081"
						bootstrap_servers = 'kfkie0z211.linux.eden:9094'
						}
					else if ((env.TAG_NAME).startsWith('ERGODEV-v')) {
						schema_registry = "https://kfkie0y311.linux.eden:8081"
						bootstrap_servers = 'kfkie0y231.linux.eden:9094'
						}
					echo "bootstrap_servers: ${bootstrap_servers}"
					echo "schema_registry: ${schema_registry}"
					
					templates.each {
						echo "template: ${it.path}"
						sh """
						python ikep_transports.py ${it.path} ${schema_registry} ${bootstrap_servers} ${schemas_dir} 
						"""
					}
				}
			}
		}

    
  }
}