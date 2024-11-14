#!/bin/bash
cp scripts/git-hooks/* .git/hooks/
chmod +x .git/hooks/*
echo "Git hooks instalados correctamente."