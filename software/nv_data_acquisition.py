#!/usr/bin/env python3
"""
Adquisición de datos del sensor NV
Comunicación serial con Arduino/Firmware

Uso:
    python3 nv_data_acquisition.py --port /dev/ttyUSB0 --duration 60
"""

import serial
import numpy as np
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

class NVSensor:
    """
    Clase principal para comunicación con sensor NV
    """
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self.buffer: List[Dict] = []
        self.calibration = self.load_calibration()
        self.callback: Optional[Callable] = None
        
    def connect(self) -> bool:
        """Establecer conexión Serial con el sensor"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            # Esperar inicialización Arduino
            time.sleep(2)
            
            # Leer mensaje de bienvenida
            welcome = self.ser.readline().decode().strip()
            print(f"Sensor: {welcome}")
            
            return True
        except serial.SerialException as e:
            print(f"Error conectando a {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Cerrar conexión Serial"""
        if self.ser:
            self.ser.close()
            self.ser = None
    
    def load_calibration(self) -> Dict:
        """Cargar calibración del sensor desde archivo"""
        cal_file = Path('sensor_calibration.json')
        if cal_file.exists():
            try:
                with open(cal_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando calibración: {e}")
        return {'offset': 0.0, 'scale': 1.0, 'timestamp': None}
    
    def save_calibration(self, offset: float, scale: float = 1.0):
        """Guardar calibración a archivo"""
        cal = {
            'offset': offset,
            'scale': scale,
            'timestamp': datetime.now().isoformat()
        }
        with open('sensor_calibration.json', 'w') as f:
            json.dump(cal, f, indent=2)
        self.calibration = cal
        print(f"Calibración guardada: offset={offset:.9f}")
    
    def send_command(self, cmd: str) -> str:
        """Enviar comando al sensor y retornar respuesta"""
        if not self.ser:
            raise ConnectionError("Sensor no conectado")
        
        self.ser.write(f"{cmd}\n".encode())
        time.sleep(0.1)
        
        # Leer respuesta
        response = self.ser.readline().decode().strip()
        return response
    
    def read_measurement(self) -> Optional[Dict]:
        """Leer una medición del sensor"""
        if not self.ser:
            return None
        
        try:
            line = self.ser.readline().decode().strip()
            if line and line.startswith('{'):
                data = json.loads(line)
                
                # Aplicar calibración
                if 'field_tesla' in data:
                    data['field_calibrated'] = (
                        data['field_tesla'] - self.calibration['offset']
                    ) * self.calibration['scale']
                
                return data
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error leyendo medición: {e}")
        
        return None
    
    def start_continuous(self):
        """Iniciar modo de medición continua"""
        response = self.send_command("START")
        print(f"Iniciado: {response}")
    
    def stop_continuous(self):
        """Detener modo de medición continua"""
        response = self.send_command("STOP")
        print(f"Detenido: {response}")
    
    def calibrate(self):
        """Ejecutar calibración del sensor"""
        print("Calibrando sensor (mantener estable)...")
        response = self.send_command("CALIBRATE")
        
        try:
            data = json.loads(response)
            if data.get('status') == 'calibrated':
                self.save_calibration(data['offset'])
            else:
                print(f"Calibración fallida: {data}")
        except json.JSONDecodeError:
            print(f"Respuesta no válida: {response}")
    
    def get_spectrum(self) -> List[Dict]:
        """Adquirir espectro ODMR completo"""
        print("Adquiriendo espectro ODMR...")
        self.send_command("SPECTRUM")
        
        spectrum = []
        collecting = False
        
        while True:
            line = self.ser.readline().decode().strip()
            
            if '"spectrum_start":true' in line:
                collecting = True
                continue
            if '"spectrum_end":true' in line:
                break
            
            if collecting and line.startswith('{'):
                try:
                    point = json.loads(line)
                    spectrum.append(point)
                except:
                    pass
        
        print(f"Espectro adquirido: {len(spectrum)} puntos")
        return spectrum
    
    def acquire_data(self, duration_seconds: float, 
                     save_file: Optional[str] = None,
                     callback: Optional[Callable] = None) -> List[Dict]:
        """
        Adquirir datos durante un tiempo determinado
        
        Args:
            duration_seconds: Tiempo de adquisición
            save_file: Archivo para guardar datos (JSON)
            callback: Función a llamar con cada medición
        
        Returns:
            Lista de mediciones
        """
        data = []
        start_time = time.time()
        measurement_count = 0
        
        print(f"Adquiriendo datos durante {duration_seconds}s...")
        print("Presiona Ctrl+C para detener\n")
        
        try:
            while time.time() - start_time < duration_seconds:
                measurement = self.read_measurement()
                
                if measurement and measurement.get('valid'):
                    data.append(measurement)
                    measurement_count += 1
                    
                    # Mostrar progreso
                    if measurement_count % 10 == 0:
                        field = measurement.get('field_calibrated', 0)
                        print(f"[{measurement_count}] Campo: {field:.6f} µT", end='\r')
                    
                    # Llamar callback si existe
                    if callback:
                        callback(measurement)
                
                time.sleep(0.01)  # Pequeña pausa
                
        except KeyboardInterrupt:
            print("\nAdquisición interrumpida por usuario")
        
        print(f"\nTotal mediciones válidas: {measurement_count}")
        
        if save_file:
            output = {
                'metadata': {
                    'start_time': datetime.fromtimestamp(start_time).isoformat(),
                    'duration': duration_seconds,
                    'port': self.port,
                    'calibration': self.calibration,
                    'total_measurements': measurement_count
                },
                'data': data
            }
            
            with open(save_file, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"Datos guardados en {save_file}")
        
        return data


def main():
    parser = argparse.ArgumentParser(description='Adquisición de datos NV Sensor')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Puerto Serial')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baudios')
    parser.add_argument('--duration', type=float, default=60, help='Duración (s)')
    parser.add_argument('--output', default='nv_data.json', help='Archivo salida')
    parser.add_argument('--calibrate', action='store_true', help='Calibrar primero')
    parser.add_argument('--spectrum', action='store_true', help='Adquirir espectro')
    
    args = parser.parse_args()
    
    # Crear sensor y conectar
    sensor = NVSensor(port=args.port, baudrate=args.baudrate)
    
    if not sensor.connect():
        print("No se pudo conectar al sensor")
        return
    
    try:
        if args.calibrate:
            sensor.calibrate()
        
        if args.spectrum:
            spectrum = sensor.get_spectrum()
            # Guardar espectro
            with open('spectrum.json', 'w') as f:
                json.dump(spectrum, f, indent=2)
            print(f"Espectro guardado en spectrum.json")
        else:
            # Modo continuo
            sensor.start_continuous()
            sensor.acquire_data(args.duration, args.output)
            sensor.stop_continuous()
            
    finally:
        sensor.disconnect()


if __name__ == '__main__':
    main()
