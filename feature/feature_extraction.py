import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.path as mpath
import numpy as np
import os
import uuid

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


def cut_image(points, image):
    height, width = image.shape[:2]
    
    # 1. Creazione della maschera (booleana)
    x, y = np.meshgrid(np.arange(width), np.arange(height))
    pix_coords = np.column_stack((x.flatten(), y.flatten()))
    path = mpath.Path(points)
    mask = path.contains_points(pix_coords).reshape(height, width)
    
    # 2. Creazione dell'immagine RGBA (Red, Green, Blue, Alpha)
    # Inizializziamo un array di zeri (completamente trasparente)
    new_image = np.zeros((height, width, 4), dtype=np.float32)
    
    # Normalizziamo l'immagine originale in scala 0-1 se è in 0-255
    # (Matplotlib lavora meglio con i float per la trasparenza)
    img_normalized = image.astype(np.float32)
    if img_normalized.max() > 1.0:
        img_normalized /= 255.0

    if len(image.shape) == 3:
        # Immagine a colori: copiamo R, G, B
        new_image[mask, :3] = img_normalized[mask]
    else:
        # Scala di grigi: copiamo il valore su R, G e B per mantenere il grigio
        for i in range(3):
            new_image[mask, i] = img_normalized[mask]
            
    # 3. Impostiamo l'Alpha a 1.0 (opaco) solo dove la maschera è True
    new_image[mask, 3] = 1.0
    
    # 4. Ritaglio dei bordi (Crop)
    pts_array = np.array(points)
    x_min, y_min = pts_array.min(axis=0).astype(int)
    x_max, y_max = pts_array.max(axis=0).astype(int)
    
    # Padding di sicurezza per non tagliare pixel sui bordi
    cropped_image = new_image[max(0, y_min):y_max, max(0, x_min):x_max]
    
    # 5. Salvataggio
    output_dir = "transparent_cuts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_path = os.path.join(output_dir, f"cut_{uuid.uuid4().hex[:8]}.png")
    
    # plt.imsave gestisce correttamente l'array RGBA
    plt.imsave(file_path, cropped_image)
    
    return file_path


if __name__ == "__main__":

    path_file = '../../img.jpg'

    # Esempio d'uso
    selector = RoiSelector(path_file)
    print(f"Punti selezionati: {list(zip(selector.punti_x, selector.punti_y))}")
    
    img = plt.imread(path_file)

    cut_image(list(zip(selector.punti_x, selector.punti_y)), img)
