#!/bin/bash

if [ ! -d ".git/hooks" ]; then
  echo "Error: El directorio .git/hooks no existe. Asegúrate de estar en un repositorio Git."
  exit 1
fi

cp scripts/git-hooks/* .git/hooks/
chmod +x .git/hooks/*
echo "Git hooks instalados correctamente."