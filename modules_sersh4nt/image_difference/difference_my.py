import cv2
import os

import numpy as np


def get_difference(img1, img2):
    # Преобразование к типу int для возможности вычитания
    img1 = np.array(img1, dtype='int')
    img2 = np.array(img2, dtype='int')
    # Берем абсолютные цифры
    absolute = np.abs(img1 - img2)
    # Складываем цифры по трем цветам в единую сущность
    result = absolute[:, :, 0:1] + absolute[:, :, 1:2] + absolute[:, :, 2:3]
    # Применим теперь нормирующую функцию с заданным коэффициентом чувствительности
    # Из-за сложения трех цветов - начальное значение может быть от 0 до 3 * 256 = 768
    # Минимальный порог чувствительности - все, что ниже него не отображаем
    sensitivity_min = 24
    # Остальное красим от 0 до 255, данный коэффициент насыщает краски
    sensitivity_rate = 5
    result2 = result - sensitivity_min
    result2[result2 < 0] = 0
    result3 = result2 * sensitivity_rate
    result3[result3 > 255] = 255
    result4_color = np.array(result3, dtype='uint8')
    result4_zero = np.zeros(shape=result4_color.shape, dtype=result4_color.dtype)
    result4 = np.concatenate((result4_zero, result4_color, result4_color), axis=2)
    print(np.mean(result))
    print(np.max(result))
    print(np.min(result))

    return result4


def crop_image(h, w, img):
    res = img.copy()
    res = res[
          (res.shape[0] - h) // 2: (res.shape[0] + h) // 2,
          (res.shape[1] - w) // 2: (res.shape[1] + w) // 2
    ]
    return res


def get_difference_images(img1, img2):
    # Обрезка по меньшему размеру
    h, w, _ = img1.shape
    h = min(h, img2.shape[0])
    w = min(w, img2.shape[1])
    crop1 = crop_image(h, w, img1)
    crop2 = crop_image(h, w, img2)
    blur = [cv2.blur(src=img1, ksize=(3, 3), dst=0), cv2.blur(src=img2, ksize=(3, 3), dst=0)]
    # blur = [img1, img2]
    # Функция сравнения
    difference = get_difference(blur[0], blur[1])
    orig_rate = 80
    dif_rate = 80
    return cv2.addWeighted(crop1, orig_rate / 100.0, difference, dif_rate / 100.0, 0.0)


# Загружаем картинки для сравнения
img = []
for root, dirs, files in os.walk("IMG"):
    files.sort()
    for file in files:
        if len(img) < 2:
            if file and file.endswith(".jpg"):
                img.append(cv2.imread(os.path.join("IMG", file)))
# Размываем немного картинки для того, чтобы избавиться от шума при сравнении


res = get_difference_images(img[0], img[1])
cv2.imwrite(os.path.join("Z_gray_res.jpg"), res)
cv2.imshow("result", res)
cv2.waitKey(0)
#
# a = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
#               15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]).reshape(4, 4, 2)
# a = np.abs(a)
# print(a)
# print(a[:, :, 1:2])
# b = np.roll(a, -1, axis=0)[:2, :]
# print(b)
# a[:2, :] += b
# print(a)

#
# def delete_me_1():
#     rost = []
#     for i in range(20):
#         rost.append(random.randint(0, 50))
#
#     knowing_count = []
#     for i in range(len(rost)):
#         count = 1
#         next_man_index = i
#         # Цикл передачи к следующему
#         while True:
#             receiver = next_man_index
#             receiver_rost = 10000000
#             # Цикл поиска следующего
#             for j in range(next_man_index + 1, len(rost)):
#                 if receiver_rost > rost[j] > rost[next_man_index]:
#                     receiver = j
#                     receiver_rost = rost[j]
#             if receiver > next_man_index:
#                 next_man_index = receiver
#                 count += 1
#             else:
#                 break
#         knowing_count.append(count)
#
#     print(rost)
#     print(knowing_count)
#








