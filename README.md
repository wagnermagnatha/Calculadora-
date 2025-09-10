FII Calculator - Kivy project
=============================

Conteúdo:
- main.py (código fonte)
- buildozer.spec (arquivo de configuração para gerar APK com Buildozer)

Instruções rápidas (Linux / WSL recommended):
1) Instalar dependências (Ubuntu/Debian example):
   sudo apt update && sudo apt install -y python3-pip python3-setuptools git build-essential    openjdk-17-jdk unzip zlib1g-dev libssl-dev libncurses5 libncurses5-dev libffi-dev

2) Instalar Buildozer e dependências Python:
   pip install --user buildozer
   pip install --user cython

3) Inicializar (opcional) e editar buildozer.spec se quiser ajustar package.name / permissions:
   buildozer init
   (ou usar o buildozer.spec já fornecido)

4) Construir APK de debug:
   buildozer -v android debug
   (o APK final ficará em ./.buildozer/android/platform/build-arm64-v8a.../bin/)

Notas importantes:
- Buildozer funciona melhor em Linux; no Windows use WSL2/Ubuntu.
- python-for-android recomenda NDK r25b (ver docs). Se tiver problemas, confira as recomendações oficiais.
- Para publicar no Google Play, siga as instruções de assinatura e uso de targetSdkVersion conforme exigido.