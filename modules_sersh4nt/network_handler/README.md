# Движок с нейронной сетью
Работает в виртуальной среде как с процессором, так и с видеокартой.
Позволяет обучать нейросеть и детектировать объекты с любого видеопотока (isb, ip камеры, фото).
Исходный код взят с репо https://github.com/ultralytics/yolov5
 
# Установка
Работа в виртуальной среде Anaconda. Установка для CPU:
```shell
conda config --add channels conda-forge
conda install pytorch torchvision cpuonly -c pytorch
```
Установка для GPU  с установленной CUDA 11.1:
```shell
conda config --add channels conda-forge
conda install pytorch torchvision cudatoolkit=11.1 -c pytorch -c conda-forge
```
Далее необходимо установить зависимости (поместить файл requirements.txt в папку с проектом)
```shell
pip install -r requirements.txt
```

# network_handler.py
**Использует полностью папки `models`, `libs` и `data`**

Класс-обработчик нейронки. При инициализации загружает в себя нейронную сеть yolov5 (веса можно найти на гитхабе https://github.com/ultralytics/yolov5).
При инициализации требует путь к корню проекта.

Распознавание через функцию `detect(img)`, принимает на вход RGB изображение в виде ndarray.

Тренировка нейросети через функцию `train_network()`.
Автоматически тренируется на изображениях из папки `data`. Сохраняет результат в папку `models/train`.
В корневой папке проекта должна быть папка data с изображениями, аннтотациями в формате yolo и файлом `classes.txt`.
Пример залит на репо. Аннотации сделаны в LabelImg, **НЕОБХОДИМО ВЫБРАТЬ ФОРМАТ YOLO**.
Конфиг и пути создает автоматически, ничего менять не надо. Необходимо просто закинуть фотки, аннотации и дополнить файл `classes.txt` в папке `data`.
