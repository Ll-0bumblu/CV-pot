import cv2
import numpy as np
import argparse

def create_mask(frame):
    # Отсечение по цвету: зеленый цвет крышек банок
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([90, 255, 255]))
    # Фильтры: убираем одиночные шумовые точки
    mask = cv2.medianBlur(mask, 5)
    return mask


def main():
    # Аргументы командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', type=str, required=True, help='Путь к видеофайлу')
    parser.add_argument('--line', type=int, default=320, help='X-координата линии подсчета')
    args = parser.parse_args()

    # Работа с видео
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print('Не удалось открыть видеофайл')
        exit()

    line_x = args.line
    count = 0
    next_id = 0
    max_dist = 60
    objects = [] # крыщки с прошлого кадра

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))
        mask = create_mask(frame)

        # Контуры
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        centers = []
        for i in range(len(contours)):
            if cv2.contourArea(contours[i]) > 500:
                x, y, w, h = cv2.boundingRect(contours[i])
                cx = x + w // 2
                cy = y + h // 2
                centers.append([cx, cy])
                cv2.drawContours(frame, contours, i, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

        new_objects = []
        used = []      # список уже занятых центров 
        # жадный поиск ближайшего
        for i in range(len(objects)):
            best_j = -1             # индекс найденной пары
            best_dist = 1000000     # дисатнция до 
            for j in range(len(centers)):
                if j in used:       # занятые центры текущего кадра
                    continue
                dist = ((centers[j][0] - objects[i]['x']) ** 2 +
                        (centers[j][1] - objects[i]['y']) ** 2) ** 0.5
                if dist < best_dist and dist < max_dist:
                    best_dist = dist
                    best_j = j
            # Проверяем, есть ли новая крышечка в кадре
            if best_j >= 0:
                used.append(best_j)
                cx = centers[best_j][0]
                cy = centers[best_j][1]
                # пересечение вертикальной линии
                crossed_left = objects[i]['x'] > line_x and cx <= line_x
                crossed_right = objects[i]['x'] < line_x and cx >= line_x
                if objects[i]['counted'] == False and (crossed_left or crossed_right):
                    count = count + 1
                    objects[i]['counted'] = True
                new_objects.append({'id': objects[i]['id'], 'x': cx, 'y': cy,
                                    'counted': objects[i]['counted']})

        for j in range(len(centers)):
            if j in used:
                continue
            new_objects.append({'id': next_id, 'x': centers[j][0],
                                'y': centers[j][1], 'counted': False})
            next_id = next_id + 1

        objects = new_objects

        # рисуем вертикальную линия подсчета и текст
        cv2.line(frame, (line_x, 0), (line_x, 480), (0, 0, 255), 2)
        cv2.putText(frame, 'Count: {}'.format(count), (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow('result', frame)
        cv2.imshow("mask", mask)

        if cv2.waitKey(30) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print('Итоговое количество объектов: {}'.format(count))


main()