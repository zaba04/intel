import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.ndimage import gaussian_filter
from scipy.ndimage import distance_transform_edt
import heapq


class AsymetricTerrainGenerator:
    def __init__(self, size=300, complexity=5):
        self.size = size
        self.complexity = complexity

    def generate_terrain(self):
        # Inicjalizacja pustej mapy
        terrain = np.zeros((self.size, self.size))

        # Generowanie nieregularnych wypiętrzeń i zagłębień
        for _ in range(self.complexity * 3):
            # Losowe parametry każdej cechy terenu
            center_x = np.random.randint(0, self.size)
            center_y = np.random.randint(0, self.size)
            amplitude = np.random.uniform(-2, 2)  # Może być ujemne (dolina) lub dodatnie (górka)

            # Nieregularny kształt
            x, y = np.meshgrid(
                np.linspace(-1, 1, self.size),
                np.linspace(-1, 1, self.size)
            )

            # Bardziej nieregularny kształt poprzez dodanie losowych składowych
            feature = amplitude * np.exp(
                -((x * np.random.uniform(0.5, 2)) ** 2 +
                  (y * np.random.uniform(0.5, 2)) ** 2) *
                np.random.uniform(3, 10)
            )

            # Przesuniecie i nałożenie cechy
            shifted_feature = np.roll(
                np.roll(feature, center_x, axis=1),
                center_y, axis=0
            )
            terrain += shifted_feature

        # Dodatkowe zniekształcenia
        terrain += np.random.normal(0, 0.2, terrain.shape)

        # Wygładzenie terenu z zachowaniem ogólnej struktury
        terrain = gaussian_filter(terrain, sigma=3)

        return terrain


class PotentialFieldNavigator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nawigator Asymetrycznego Terenu")
        self.setGeometry(100, 100, 800, 700)

        # Główny widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Główny layout
        main_layout = QVBoxLayout(main_widget)

        # Layout dla przycisków
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # Przycisk generowania pola
        self.generate_button = QPushButton("Generuj Asymetryczny Teren")
        self.generate_button.clicked.connect(self.generate_potential_field)
        button_layout.addWidget(self.generate_button)

        # Etykieta statusu
        self.status_label = QLabel("Naciśnij 'Generuj Asymetryczny Teren'")
        button_layout.addWidget(self.status_label)

        # Figura Matplotlib
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # Początkowe ustawienia
        self.potential_field = None
        self.ax = self.figure.add_subplot(111)
        self.path_line = None
        self.terrain_generator = AsymetricTerrainGenerator()

    def generate_potential_field(self):
        try:
            # Czyszczenie poprzedniego wykresu
            self.ax.clear()

            # Generowanie asymetrycznego terenu
            self.potential_field = self.terrain_generator.generate_terrain()

            # Wizualizacja
            im = self.ax.imshow(
                self.potential_field,
                cmap='RdYlGn_r',  # Czerwony (wysoki potencjał) - zielony (niski potencjał)
                extent=[0, 10, 0, 10],
                origin='lower'
            )
            self.figure.colorbar(im, ax=self.ax, label='Potencjał')
            self.ax.set_title('Całkowicie Asymetryczny Teren')
            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')

            # Podłączenie zdarzenia kliknięcia
            self.canvas.mpl_connect('button_press_event', self.find_optimal_path)

            # Odświeżenie Canvas
            self.canvas.draw()

            # Aktualizacja etykiety statusu
            self.status_label.setText("Asymetryczny teren wygenerowany. Kliknij na mapie.")
            self.status_label.setStyleSheet("color: green;")

        except Exception as e:
            # Wyświetlenie szczegółowego błędu
            error_msg = f"Błąd: {str(e)}"
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("color: red;")
            print(error_msg)

    # def find_optimal_path(self, event):
    #     if self.potential_field is not None and event.inaxes:
    #         try:
    #             # Usunięcie poprzedniej ścieżki
    #             if self.path_line:
    #                 self.path_line.remove()
    #
    #             # Współrzędne pikseli
    #             start_x = int(event.xdata / 10 * 300)
    #             start_y = int(event.ydata / 10 * 300)
    #
    #             # Znajdź globalnie najniższy punkt
    #             min_index = np.unravel_index(
    #                 np.argmin(self.potential_field),
    #                 self.potential_field.shape
    #             )
    #             min_x = min_index[1]
    #             min_y = min_index[0]
    #
    #             # Oblicz ścieżkę o najmniejszym potencjale
    #             path = self._find_lowest_potential_path(
    #                 (start_x, start_y),
    #                 (min_x, min_y)
    #             )
    #
    #             # Konwersja współrzędnych pikseli na współrzędne wykresu
    #             path_x = [p[1] / 300 * 10 for p in path]
    #             path_y = [p[0] / 300 * 10 for p in path]
    #
    #             # Narysuj ścieżkę
    #             self.path_line, = self.ax.plot(
    #                 path_x, path_y,
    #                 'k-',
    #                 linewidth=3,
    #                 alpha=0.7
    #             )
    #             self.canvas.draw()
    #
    #             # Aktualizacja etykiety statusu
    #             self.status_label.setText(
    #                 f"Ścieżka o najmniejszym potencjale z ({event.xdata:.2f}, {event.ydata:.2f}) do ({min_x/300*10:.2f}, {min_y/300*10:.2f})"
    #             )
    #             self.status_label.setStyleSheet("color: blue;")
    #
    #         except Exception as e:
    #             error_msg = f"Błąd przy wyznaczaniu ścieżki: {str(e)}"
    #             self.status_label.setText(error_msg)
    #             self.status_label.setStyleSheet("color: red;")
    #             print(error_msg)

    def find_optimal_path(self, event):
        if self.potential_field is not None and event.inaxes:
            try:
                # Usunięcie poprzedniej ścieżki
                if self.path_line:
                    self.path_line.remove()

                # Współrzędne pikseli dla miejsca kliknięcia
                start_x = int(event.xdata / 10 * self.terrain_generator.size)
                start_y = int(event.ydata / 10 * self.terrain_generator.size)

                # Znajdź punkt o najniższym potencjale
                min_index = np.unravel_index(
                    np.argmin(self.potential_field),
                    self.potential_field.shape
                )
                goal_x, goal_y = min_index[1], min_index[0]

                # Wyznaczenie ścieżki
                path = self._find_lowest_potential_path(
                    (start_y, start_x),
                    (goal_y, goal_x)
                )

                # Konwersja ścieżki na współrzędne wykresu
                path_x = [p[1] / self.terrain_generator.size * 10 for p in path]
                path_y = [p[0] / self.terrain_generator.size * 10 for p in path]

                # Narysowanie ścieżki
                self.path_line, = self.ax.plot(
                    path_x, path_y, 'k-', linewidth=3, alpha=0.7
                )
                self.canvas.draw()

                # Aktualizacja statusu
                self.status_label.setText(
                    f"Ścieżka z ({event.xdata:.2f}, {event.ydata:.2f}) do ({goal_x / self.terrain_generator.size * 10:.2f}, {goal_y / self.terrain_generator.size * 10:.2f})"
                )
                self.status_label.setStyleSheet("color: blue;")

            except Exception as e:
                error_msg = f"Błąd przy wyznaczaniu ścieżki: {str(e)}"
                self.status_label.setText(error_msg)
                self.status_label.setStyleSheet("color: red;")
                print(error_msg)

    def _find_lowest_potential_path(self, start, goal, max_iterations=10000):
        def get_neighbors(point):
            x, y = point
            neighbors = [
                (x+1, y), (x-1, y),
                (x, y+1), (x, y-1),
                (x+1, y+1), (x-1, y-1),
                (x+1, y-1), (x-1, y+1)
            ]
            return [
                (nx, ny) for nx, ny in neighbors
                if 0 <= nx < self.potential_field.shape[1] and
                   0 <= ny < self.potential_field.shape[0]
            ]

        current = start
        path = [current]
        visited = set([current])

        for _ in range(max_iterations):
            if current == goal:
                break

            # Znajdź sąsiada z najmniejszym potencjałem, który nie był odwiedzony
            neighbors = get_neighbors(current)
            unvisited_neighbors = [
                n for n in neighbors
                if n not in visited
            ]

            if not unvisited_neighbors:
                break

            unvisited_neighbors.append(current)

            # Wybierz sąsiada z najmniejszym potencjałem
            next_point = min(
                unvisited_neighbors,
                key=lambda p: self.potential_field[p[1], p[0]]
            )

            path.append(next_point)
            visited.add(next_point)
            current = next_point

        return path


    # def _find_lowest_potential_path(self, start, goal, max_iterations=50000):
    #     def heuristic(p1, p2):
    #         # Funkcja heurystyczna: odległość euklidesowa
    #         return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
    #
    #     def get_neighbors(point):
    #         x, y = point
    #         neighbors = [
    #             (x + 1, y), (x - 1, y),
    #             (x, y + 1), (x, y - 1),
    #             (x + 1, y + 1), (x - 1, y - 1),
    #             (x + 1, y - 1), (x - 1, y + 1)
    #         ]
    #         # Upewnij się, że sąsiedzi są w granicach mapy
    #         return [
    #             (nx, ny) for nx, ny in neighbors
    #             if 0 <= nx < self.potential_field.shape[0] and
    #                0 <= ny < self.potential_field.shape[1]
    #         ]
    #
    #     # Priority queue (kolejka priorytetowa)
    #     open_set = []
    #     heapq.heappush(open_set, (0, start))  # (priorytet, punkt)
    #
    #     came_from = {}
    #     g_score = {start: 0}
    #     f_score = {start: heuristic(start, goal)}
    #
    #     iterations = 0
    #
    #     while open_set:
    #         iterations += 1
    #         if iterations > max_iterations:
    #             print("Przekroczono maksymalną liczbę iteracji")
    #             break
    #
    #         # Wyciągnij punkt z najniższym f_score
    #         _, current = heapq.heappop(open_set)
    #
    #         if current == goal:
    #             # Odtwórz ścieżkę
    #             path = []
    #             while current in came_from:
    #                 path.append(current)
    #                 current = came_from[current]
    #             path.append(start)
    #             return path[::-1]
    #
    #         for neighbor in get_neighbors(current):
    #             tentative_g_score = g_score[current] + self.potential_field[neighbor]
    #
    #             if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
    #                 came_from[neighbor] = current
    #                 g_score[neighbor] = tentative_g_score
    #                 f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
    #                 heapq.heappush(open_set, (f_score[neighbor], neighbor))
    #
    #     print("Ścieżka nie została znaleziona.")
    #     return []  # Brak ścieżki
    #

def main():
    app = QApplication(sys.argv)
    main_window = PotentialFieldNavigator()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()