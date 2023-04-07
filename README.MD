# cubeFW
## Einführung
cubeFW ist ein Projekt im Rahmen meiner Masterarbeit, das sich mit der Entwicklung eines Versuchsstandes für Mikrofunkenerosion namens CUBE befasst. Das Projekt besteht aus zwei Hauptkomponenten: der Firmware für einen ESP32-Mikrocontroller und einer zugehörigen GUI-Anwendung (CUBEcontrol) für die Steuerung des Versuchsstandes. Die Firmware ist verantwortlich für die Steuerung der Hardware und Elektronik des Versuchsstandes, während die GUI-Anwendung in Python und Tkinter geschrieben ist und über eine serielle Schnittstelle mit der ESP32-Firmware unter Verwendung von Gcodes kommuniziert.

## Komponenten
### ESP32 Firmware
Die Firmware für den ESP32-Mikrocontroller steuert die Hardware und Elektronik des CUBE-Versuchsstandes. Sie kommuniziert mit der CUBEcontrol-GUI-Anwendung über eine serielle Schnittstelle unter Verwendung von Gcodes. Die Firmware kann mit PlatformIO kompiliert und auf den Mikrocontroller hochgeladen werden.

### CUBEcontrol GUI-Anwendung
CUBEcontrol ist eine in Python und Tkinter geschriebene GUI-Anwendung zur Steuerung des CUBE-Versuchsstandes. Sie ermöglicht die Kommunikation mit der ESP32-Firmware über eine serielle Schnittstelle unter Verwendung von Gcodes. Die Anwendung kann für Windows als Single-File-Application mit PyInstaller gebündelt werden.

## Installation
### Voraussetzungen
- Python 3.x
- Tkinter
- PySerial
- sv-ttk
- PyInstaller (optional, für die Erstellung einer Single-File-Application)
- PlatformIO (für die Kompilierung und Hochladen der ESP32-Firmware)

### Anweisungen
1. Klonen Sie das Repository:

    ```console
    git clone https://github.com/yourusername/cubeFW.git
    cd cubeFW
    ```

2. Installieren Sie die erforderlichen Python-Pakete:
    ```console
    pip install -r requirements.txt
    ```

3. Um die CUBEcontrol-GUI-Anwendung als Single-File-Application für Windows zu erstellen, führen Sie den folgenden Befehl aus:
    ```console
    pyinstaller cubeControl.spec
    ```
    Nach erfolgreicher Kompilierung finden Sie die Single-File-Application im dist-Ordner.

4. Für die Kompilierung und das Hochladen der ESP32-Firmware stellen Sie sicher, dass PlatformIO installiert ist. Wechseln Sie in das Verzeichnis, das die platformio.ini-Datei enthält, und führen Sie den folgenden Befehl aus:
    ```console
    platformio run --target upload
    ```
    Dies kompiliert die Firmware und lädt sie auf den ESP32-Mikrocontroller hoch.

### Verwendung
1. Starten Sie die CUBEcontrol-GUI-Anwendung, indem Sie die erstellte Single-File-Application ausführen oder cubeControl.py direkt ausführen:
    ```console
    python cubeControl.py
    ```
2. Stellen Sie sicher, dass der CUBE-Versuchsstand eingeschaltet und mit dem Computer verbunden ist.

3. Wählen Sie in der CUBEcontrol-GUI-Anwendung die entsprechende serielle Schnittstelle aus und stellen Sie eine Verbindung her.

4. Sie können nun den CUBE-Versuchsstand über die GUI-Anwendung steuern und Gcodes senden, um die Hardware und Elektronik des Versuchsstandes zu steuern.