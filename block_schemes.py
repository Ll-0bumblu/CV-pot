import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'
from matplotlib.patches import Rectangle, Ellipse, Polygon, FancyArrowPatch

SCALE = 0.5   # дюймов на единицу данных
FS = 6        # кегль текста


def text_size(fig, text):
    """Реальный размер текста в единицах данных"""
    t = fig.text(0, 0, text, fontsize=FS, linespacing=1.3)
    bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    t.remove()
    return bb.width / fig.dpi / SCALE, bb.height / fig.dpi / SCALE


def node(fig, ax, x, y, text, kind='proc'):
    tw, th = text_size(fig, text)
    if kind == 'proc':  w, h = tw + 0.7, th + 0.5
    elif kind == 'io':  w, h = tw + 1.2, th + 0.5
    elif kind == 'dec': w, h = 2*tw + 0.7, 2*th + 0.7   # ромб ~вдвое больше текста
    else:               w, h = 1.5*tw + 0.5, 2.2*th + 0.35
    if kind == 'start':
        p = Ellipse((x, y), w, h, facecolor='white', edgecolor='black', lw=1.3, zorder=1)
    elif kind == 'io':
        s = 0.3
        p = Polygon([(x-w/2+s, y+h/2), (x+w/2+s, y+h/2), (x+w/2-s, y-h/2), (x-w/2-s, y-h/2)],
                    closed=True, facecolor='white', edgecolor='black', lw=1.3, zorder=1)
    elif kind == 'dec':
        p = Polygon([(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)],
                    closed=True, facecolor='white', edgecolor='black', lw=1.3, zorder=1)
    else:
        p = Rectangle((x-w/2, y-h/2), w, h, facecolor='white', edgecolor='black', lw=1.3, zorder=1)
    ax.add_patch(p)
    ax.text(x, y, text, ha='center', va='center', fontsize=FS, linespacing=1.3, zorder=3)
    return {'x': x, 'y': y, 'w': w, 'h': h, 'tw': tw, 'th': th, 'kind': kind, 'text': text}


def anch(n, side):
    return {'top': (n['x'], n['y']+n['h']/2), 'bottom': (n['x'], n['y']-n['h']/2),
            'left': (n['x']-n['w']/2, n['y']), 'right': (n['x']+n['w']/2, n['y'])}[side]


def connect(ax, pts, label=None, lx=0, ly=0):
    for i in range(len(pts)-2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]], color='black', lw=1.2, zorder=2)
    ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle='-|>', mutation_scale=13,
                                 lw=1.2, color='black', shrinkA=0, shrinkB=0, zorder=2))
    if label:
        ax.text(lx, ly, label, fontsize=FS, ha='center', va='center', style='italic', zorder=3)


def down(ax, a, b, label=None):
    p1, p2 = anch(a, 'bottom'), anch(b, 'top')
    connect(ax, [p1, p2], label, p1[0]+0.3, (p1[1]+p2[1])/2)


def right_branch(ax, a, b, label):
    p1, p2 = anch(a, 'right'), anch(b, 'left')
    connect(ax, [p1, p2], label, (p1[0]+p2[0])/2, p1[1]+0.28)


def node_h(fig, text, kind):
    tw, th = text_size(fig, text)
    if kind in ('proc', 'io'): return th + 0.5
    if kind == 'dec':          return 2*th + 0.7
    return 2.2*th + 0.35


def column(fig, ax, items, gap=0.85):
    """Вертикальная колонка блоков с автоматическим шагом по высоте"""
    nodes, y = [], 0.0
    for text, kind in items:
        h = node_h(fig, text, kind)
        cy = y - h/2
        nodes.append(node(fig, ax, 0, cy, text, kind))
        y = cy - h/2 - gap
    return nodes


def finish(fig, ax, nodes, extra_x=(), fname='out.png'):
    xmin = min([n['x']-n['w']/2 for n in nodes] + list(extra_x)) - 0.6
    xmax = max([n['x']+n['w']/2 for n in nodes] + list(extra_x)) + 0.6
    ymin = min(n['y']-n['h']/2 for n in nodes) - 0.6
    ymax = max(n['y']+n['h']/2 for n in nodes) + 0.6
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_aspect('equal'); ax.axis('off')
    fig.set_size_inches((xmax-xmin)*SCALE, (ymax-ymin)*SCALE)
    fig.savefig(fname, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def check_fit(nodes):
    ok = True
    for n in nodes:
        tw, th, w, h, k = n['tw'], n['th'], n['w'], n['h'], n['kind']
        if k == 'proc':  fit = tw <= w-0.4 and th <= h-0.3
        elif k == 'io':  fit = tw <= w-0.9 and th <= h-0.3
        elif k == 'dec': fit = tw/w + th/h <= 0.95
        else:            fit = (tw/w)**2 + (th/h)**2 <= 0.85
        if not fit:
            ok = False
            print('НЕ ВЛЕЗАЕТ:', n['text'])
    return ok


def new_fig():
    return plt.subplots(figsize=(1, 1))


# ================= Схема 2: create_mask =================
fig, ax = new_fig()
ns = column(fig, ax, [
    ('Начало create_mask', 'start'),
    ('Вход: кадр BGR', 'io'),
    ('Перевод BGR → HSV', 'proc'),
    ('inRange: H 35–90,\nS 40–255, V 40–255', 'proc'),
    ('Медианный фильтр 5×5', 'proc'),
    ('Выход: бинарная маска', 'io'),
    ('Конец', 'start')])
for a, b in zip(ns, ns[1:]):
    down(ax, a, b)
print('scheme2 fit:', check_fit(ns))
finish(fig, ax, ns, fname='scheme_2_create_mask.png')

# ================= Схема 1: main =================
fig, ax = new_fig()
ns = column(fig, ax, [
    ('Начало', 'start'),
    ('Ввод аргументов\n--video, --line', 'io'),
    ('Открыть видеофайл', 'proc'),
    ('Видео открыто?', 'dec'),
    ('count=0, next_id=0,\nobjects=[]', 'proc'),
    ('Чтение кадра', 'proc'),
    ('Кадр прочитан?', 'dec'),
    ('resize 640×480;\ncreate_mask', 'proc'),
    ('Контуры; площадь>500;\nвычисление центров', 'proc'),
    ('Сопоставление и подсчёт;\nрегистрация новых', 'proc'),
    ('Отрисовка; imshow', 'proc'),
    ('Нажата «q»?', 'dec'),
    ('release; destroyAllWindows;\nвывод итога', 'proc'),
    ('Конец', 'start')])
n1,n2,n3,n4,n5,n6,n7,n8,n9,n10,n11,n12,n13,n14 = ns

lane7 = max(n7['w'], n13['w'])/2 + 0.8
err_w = text_size(fig, 'Сообщение\nоб ошибке')[0] + 0.7
err = node(fig, ax, lane7 + 0.7 + err_w/2, n4['y'], 'Сообщение\nоб ошибке')
xlane = -max(n['w'] for n in ns)/2 - 1.0

down(ax, n1, n2); down(ax, n2, n3); down(ax, n3, n4)
down(ax, n4, n5, 'Да')
right_branch(ax, n4, err, 'Нет')
connect(ax, [anch(err, 'bottom'), (err['x'], n14['y']), anch(n14, 'right')])
down(ax, n5, n6); down(ax, n6, n7)
down(ax, n7, n8, 'Да')
connect(ax, [anch(n7, 'right'), (lane7, n7['y']), (lane7, n13['y']), anch(n13, 'right')],
        'Нет', (n7['x']+n7['w']/2+lane7)/2, n7['y']+0.28)
down(ax, n8, n9); down(ax, n9, n10); down(ax, n10, n11); down(ax, n11, n12)
down(ax, n12, n13, 'Да')
connect(ax, [anch(n12, 'left'), (xlane, n12['y']), (xlane, n6['y']), anch(n6, 'left')],
        'Нет', (n12['x']-n12['w']/2+xlane)/2, n12['y']+0.28)
down(ax, n13, n14)
print('scheme1 fit:', check_fit(ns + [err]))
finish(fig, ax, ns + [err], extra_x=(xlane,), fname='scheme_1_main.png')

# ================= Схема 3: сопоставление и подсчёт =================
fig, ax = new_fig()
ms = column(fig, ax, [
    ('Начало цикла по крышкам', 'start'),
    ('best_j=−1, best_dist=∞;\nпоиск ближайшего центра', 'proc'),
    ('Пара найдена?\n(dist < 60)', 'dec'),
    ('Линия пересечена\nи counted=False?', 'dec'),
    ('Обновить координаты;\nцентр → used', 'proc'),
    ('Конец (следующая крышка)', 'start')])
m1,m2,m3,m4,m5,m6 = ms

cnt_w = text_size(fig, 'count+1;\ncounted=True')[0] + 0.7
cnt = node(fig, ax, m4['w']/2 + 0.9 + cnt_w/2, m4['y'], 'count+1;\ncounted=True')
rem_w = text_size(fig, 'Крышка удаляется\nиз памяти')[0] + 0.7
rem_x = max(m3['w']/2 + 1.0 + rem_w/2, cnt['x'] + cnt['w']/2 + 0.7 + rem_w/2)
rem = node(fig, ax, rem_x, m3['y'], 'Крышка удаляется\nиз памяти')

down(ax, m1, m2); down(ax, m2, m3)
down(ax, m3, m4, 'Да')
right_branch(ax, m3, rem, 'Нет')
connect(ax, [anch(rem, 'bottom'), (rem['x'], m6['y']), anch(m6, 'right')])
down(ax, m4, m5, 'Нет')
right_branch(ax, m4, cnt, 'Да')
connect(ax, [anch(cnt, 'bottom'), (cnt['x'], m5['y']), anch(m5, 'right')])
down(ax, m5, m6)
print('scheme3 fit:', check_fit(ms + [cnt, rem]))
finish(fig, ax, ms + [cnt, rem], fname='scheme_3_matching.png')

print('Готово: scheme_1_main.png, scheme_2_create_mask.png, scheme_3_matching.png')