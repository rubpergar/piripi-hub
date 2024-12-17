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

Cuando termine de cargar y salgan todos los contenedores en Started, abrir un navegador y poner en la barra de búsqueda `localhost`.


## Instalación de hooks de Git

Para asegurarte de que los hooks de Git estén configurados correctamente, ejecuta el siguiente comando después de clonar el repositorio:

```bash
ls -ld .git/hooks/
./scripts/git-hooks/install-hooks.sh
