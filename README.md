# Quantum NV Sensor - Sistema de Navegación Submarina

Sistema de navegación cuántica basado en centros NV (Nitrogen-Vacancy) de diamante para mapeo 3D de trayectorias submarinas sin GPS.

## 🌊 Características

- **Sensor cuántico**: Diamante NV de 3x3x0.5mm
- **Precisión**: ~1-10 metros por hora (sin corrección)
- **Fusión de sensores**: Magnetómetro + Giroscopio + Acelerómetro
- **Visualización 3D**: Trayectoria en tiempo real con Plotly
- **Coste**: ~330€ (versión DIY) a ~1350€ (versión profesional)

## 📁 Estructura del Proyecto

```
quantum-nv-sensor/
├── firmware/           # Código Arduino
│   └── nv_sensor_firmware.ino
├── software/           # Código Python
│   ├── nv_data_acquisition.py    # Adquisición de datos
│   ├── quantum_navigator.py      # Navegación y mapeo 3D
│   └── magnetic_calibration.py   # Calibración
├── hardware/           # Diseños 3D, esquemas
├── docs/              # Documentación
└── README.md
```

## 🚀 Inicio Rápido

### 1. Hardware

Ver documentación detallada en `docs/` para lista completa de componentes y guía de construcción.

**Componentes principales:**
- Diamante NV (3x3x0.5mm) - [Adamas Nano](https://www.adamasnano.com/)
- Láser 532nm - [Thorlabs CPS532](https://www.thorlabs.com/thorproduct.cfm?partnumber=CPS532)
- Fotodiodo APD - [Thorlabs PDA36A2](https://www.thorlabs.com/thorproduct.cfm?partnumber=PDA36A2)
- Raspberry Pi 4 / Arduino Due

### 2. Firmware

```bash
# Cargar en Arduino/Raspberry Pi
# Abrir firmware/nv_sensor_firmware.ino en Arduino IDE
# Seleccionar placa: Arduino Due (o Raspberry Pi Pico)
# Compilar y subir
```

### 3. Software Python

```bash
# Instalar dependencias
pip3 install numpy plotly filterpy scipy pyserial

# Adquirir datos
python3 software/nv_data_acquisition.py --port /dev/ttyUSB0 --duration 60

# Visualizar trayectoria
python3 software/quantum_navigator.py --input nv_data.json

# Simular inmersión (para pruebas)
python3 software/quantum_navigator.py --simulate --duration 120
```

## 📊 Uso

### Modo Adquisición

```python
from nv_data_acquisition import NVSensor

sensor = NVSensor(port='/dev/ttyUSB0')
sensor.connect()
sensor.calibrate()  # Calibrar antes de usar
sensor.start_continuous()
data = sensor.acquire_data(duration_seconds=300, save_file='dive.json')
sensor.stop_continuous()
sensor.disconnect()
```

### Modo Navegación

```python
from quantum_navigator import QuantumNavigator

nav = QuantumNavigator(dt=0.1)

# En bucle de adquisición:
while diving:
    mag_field = sensor.read_magnetic_field()  # [Bx, By, Bz] en Tesla
    gyro = imu.read_gyroscope()               # [wx, wy, wz] en rad/s
    accel = imu.read_accelerometer()          # [ax, ay, az] en m/s²
    
    position = nav.update(mag_field, gyro, accel)
    print(f"Posición: {position}")

# Guardar y visualizar
nav.save_trajectory('dive.json')
nav.plot_3d_trajectory('trayectoria.html')
```

## 🔬 Principio de Funcionamiento

1. **Excitación**: Láser verde (532nm) excita centros NV en el diamante
2. **Fluorescencia**: Los centros NV emiten luz roja (637nm)
3. **ODMR**: Microondas (2.87 GHz) modifican la intensidad de fluorescencia
4. **Detección**: El campo magnético desplaza la frecuencia de resonancia
5. **Navegación**: Filtro de Kalman fusiona magnetómetro + IMU para estimar posición

## 📚 Documentación

- [Guía de construcción completa](docs/build_guide.md)
- [Teoría de operación](docs/theory.md)
- [Referencia de API](docs/api_reference.md)
- [Solución de problemas](docs/troubleshooting.md)

## 🔗 Referencias

- [Proyecto Uncut Gem](https://github.com/QuantumVillage/UncutGem) - Open source quantum sensor
- [Paper IOP](https://iopscience.iop.org/article/10.1088/1361-6404/acbe7c) - Low-cost NV setup
- [Quantum Village](https://quantumvillage.org/) - Comunidad y recursos

## 📝 Licencia

MIT License - Ver LICENSE

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Abre un issue o pull request.

---

Desarrollado con 🖤 por Hartz
