<div align="center">

  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml)</a>
  
</div>

<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

## Lanzar la aplicación

Primero hay que instalar todas las dependencias: 

   ```bash
   pip install -r requirements.txt
   ```
Copiar el .env para local: 

   ```bash
   cp .env.local.example .env
   ```

Para consigurar la base de datos hacemos lo siguiente: 

   - Instalar y configurar MariaDB:
      ```sudo apt install mariadb-server -y
      sudo systemctl start mariadb
      sudo mysql_secure_installation
      ```

   - Hacemos log in en MySQL:
     ```bash
     mysql -u root -p
     ```

   - Creamos una nueva base de datos:
     ```sql
     CREATE DATABASE uvlhub;
     ```

   - Crear un usuario y otorgar privilegios:
     ```sql
     CREATE USER 'uvlhub_user'@'localhost' IDENTIFIED BY 'uvlhub_password';
     GRANT ALL PRIVILEGES ON uvlhub.* TO 'uvlhub_user'@'localhost';
     FLUSH PRIVILEGES;
     ```

   - Verificar el usuario y la base de datos: 
     ```sql
     SHOW DATABASES;
     SHOW GRANTS FOR 'uvlhub_user'@'localhost';
     ```

Configurar el .env:

   - Abrimos el archivo `.env` y establecemos las siguientes variables: 
   ```env
   MARIADB_HOSTNAME=127.0.0.1
   MARIADB_PORT=3306
   MARIADB_DATABASE=uvlhub
   MARIADB_USER=uvlhub_user
   MARIADB_PASSWORD=uvlhub_password
   ```

Aplicamos las migraciones:

   ```bash
   flask db upgrade
   ```

Poblamos la base de datos:

   ```bash
   rosemary db:seed
   ```

Para lanzar la aplicación tenemos que seguir el siguiente comando: 

   ```bash
  flask run --host=0.0.0.0 --reload --debug
   ```
Esto lanzará el servidor web, accediendo en un navegador a `http://localhost:5000` podremos ver la aplicación.


## Despliegue con Docker

Para desplegar con docker tenemos que ejecutar los siguientes comandos:


   ```bash
   cp .env.docker.example .env
   docker compose -f docker/docker-compose.dev.yml up -d --build
   ```

Si sale un error del puerto 3306 aplicar los siguientes comandos: 


   ```bash
   sudo lsof -i :3306
   sudo kill -9 <PID>
   ```
Volver a ejecutar el comando: 


   ```bash
   docker compose -f docker/docker-compose.dev.yml up -d --build
   ```

Cuando termine de cargar y salgan todos los contenedores en Started, abrir un navegador y poner en la barra de búsqueda `http://localhost`.


## Instalación de hooks de Git

Para asegurarte de que los hooks de Git estén configurados correctamente, ejecuta el siguiente comando después de clonar el repositorio:

```bash
ls -ld .git/hooks/
./scripts/git-hooks/install-hooks.sh
