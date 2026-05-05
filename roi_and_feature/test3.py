import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class RoiSelector:
    def __init__(self, image_path):
        self.img = mpimg.imread(image_path)
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.img)
        
        self.punti_x = []
        self.punti_y = []
        
        # Linea definitiva (quella che resta)
        self.linea_def, = self.ax.plot([], [], 'ro-', markersize=4)
        # Linea "elastica" (quella che segue il mouse)
        self.linea_temp, = self.ax.plot([], [], 'r--', alpha=0.5)
        
        # Connessione eventi
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_move)
        
        self.roi_done = False

        plt.title("Click SX: punto | Click DX: chiudi | ESC: esci")
        plt.show()

    def on_click(self, event):
        if not self.roi_done:
            # 1. Ignora se il click è fuori dagli assi
            if event.inaxes != self.ax: 
                return
            
            # 2. Ignora se lo strumento Zoom o Pan è attivo
            # Se mode è diverso da una stringa vuota, l'utente sta navigando
            if self.fig.canvas.toolbar.mode != "":
                return

            # Click sinistro: aggiungi punto
            if event.button == 1:
                self.punti_x.append(event.xdata)
                self.punti_y.append(event.ydata)
                self.linea_def.set_data(self.punti_x, self.punti_y)
                self.fig.canvas.draw()
                
            # Click destro: chiudi poligono e termina
            elif event.button == 3 and len(self.punti_x) > 2:
                self.punti_x.append(self.punti_x[0])
                self.punti_y.append(self.punti_y[0])
                self.linea_def.set_data(self.punti_x, self.punti_y)
                self.linea_temp.set_data([], []) # Rimuovi l'elastico
                self.fig.canvas.draw()
                self.roi_done = True
                print("ROI completata!")


    def on_move(self, event):
        if not self.roi_done:
            if event.inaxes != self.ax or len(self.punti_x) == 0:
                return
            
            # Aggiorna la linea elastica dall'ultimo punto alla posizione del mouse
            self.linea_temp.set_data([self.punti_x[-1], event.xdata], 
                                    [self.punti_y[-1], event.ydata])
            self.fig.canvas.draw()


if __name__ == "__main__":

    # Esempio d'uso
    selector = RoiSelector('img.jpg')
    print(f"Punti selezionati: {list(zip(selector.punti_x, selector.punti_y))}")
