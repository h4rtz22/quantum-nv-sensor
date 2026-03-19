#!/usr/bin/env python3
"""
Sistema Completo de Mapeo Submarino
Combina sensor NV + IMU + GPS (superficie) para navegación 3D

Uso:
    python3 submarine_mapper.py --mode real --port /dev/ttyUSB0
    python3 submarine_mapper.py --mode simulate
"""

import numpy as np
import json
import time
import argparse
import serial
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque

# Visualization
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Filter
from filterpy.kalman import KalmanFilter, ExtendedKalmanFilter
from filterpy.common import Q_discrete_white_noise


@dataclass
class SensorData:
    """Datos crudos de todos los sensores"""
    timestamp: float
    magnetic_field: np.ndarray  # [Bx, By, Bz] in Tesla
    gyro: np.ndarray           # [wx, wy, wz] in rad/s
    accel: np.ndarray          # [ax, ay, az] in m/s²
    pressure: float            # Depth in meters
    temperature: float         # Sensor temp in Celsius
    gps_position: Optional[Tuple[float, float, float]] = None  # (lat, lon, alt) only at surface


@dataclass
class NavigationState:
    """Estado estimado de navegación"""
    timestamp: float
    position: np.ndarray       # [x, y, z] in meters (NED frame)
    velocity: np.ndarray       # [vx, vy, vz] in m/s
    orientation: np.ndarray    # [roll, pitch, yaw] in radians
    magnetic_field: np.ndarray # Current magnetic reading
    confidence: float          # 0-1 confidence level
    at_surface: bool           # True if GPS available


class MagneticMap:
    """
    Mapa magnético del área de buceo
    Permite convertir B(x,y,z) -> posición
    """
    
    def __init__(self, map_file: Optional[str] = None):
        self.grid_points: List[Tuple[float, float, float]] = []  # (x, y, z)
        self.magnetic_values: List[np.ndarray] = []  # (Bx, By, Bz)
        self.bounds: Optional[Tuple] = None
        
        if map_file and Path(map_file).exists():
            self.load(map_file)
    
    def add_calibration_point(self, position: np.ndarray, magnetic_field: np.ndarray):
        """Añadir punto de calibración al mapa"""
        self.grid_points.append(tuple(position))
        self.magnetic_values.append(magnetic_field)
        self._update_bounds()
    
    def _update_bounds(self):
        """Actualizar límites del mapa"""
        if not self.grid_points:
            return
        
        points = np.array(self.grid_points)
        self.bounds = (
            (points[:, 0].min(), points[:, 0].max()),
            (points[:, 1].min(), points[:, 1].max()),
            (points[:, 2].min(), points[:, 2].max())
        )
    
    def magnetic_to_position(self, magnetic_field: np.ndarray, 
                            initial_guess: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Encontrar posición más probable dado campo magnético
        Usa búsqueda del vecino más cercano + interpolación
        """
        if len(self.grid_points) < 3:
            # Sin mapa suficiente, usar modelo simple
            return self._simple_model(magnetic_field)
        
        # Encontrar punto más cercano
        distances = [np.linalg.norm(m - magnetic_field) for m in self.magnetic_values]
        nearest_idx = np.argmin(distances)
        
        # Interpolación ponderada por distancia
        weights = np.exp(-np.array(distances) / np.std(distances))
        weights /= weights.sum()
        
        position = np.zeros(3)
        for i, (p, w) in enumerate(zip(self.grid_points, weights)):
            position += np.array(p) * w
        
        return position
    
    def _simple_model(self, magnetic_field: np.ndarray) -> np.ndarray:
        """Modelo simple cuando no hay mapa detallado"""
        # Asumir gradiente lineal del campo terrestre
        # Esto es una aproximación muy burda
        scale = np.array([1000, 1000, 500])  # m/T
        return magnetic_field * scale
    
    def save(self, filename: str):
        """Guardar mapa a archivo JSON"""
        data = {
            'grid_points': [list(p) for p in self.grid_points],
            'magnetic_values': [list(m) for m in self.magnetic_values],
            'bounds': self.bounds
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filename: str):
        """Cargar mapa desde archivo"""
        with open(filename) as f:
            data = json.load(f)
        
        self.grid_points = [tuple(p) for p in data['grid_points']]
        self.magnetic_values = [np.array(m) for m in data['magnetic_values']]
        self.bounds = data.get('bounds')
    
    def visualize(self):
        """Visualizar mapa magnético 3D"""
        if len(self.grid_points) < 2:
            print("Mapa vacío, nada que visualizar")
            return
        
        points = np.array(self.grid_points)
        magnitudes = [np.linalg.norm(m) * 1e6 for m in self.magnetic_values]  # µT
        
        fig = go.Figure(data=[go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode='markers',
            marker=dict(
                size=5,
                color=magnitudes,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='|B| (µT)')
            ),
            text=[f"B={b:.1f}µT" for b in magnitudes],
            hovertemplate='%{text}<br>X:%{x:.1f}<br>Y:%{y:.1f}<br>Z:%{z:.1f}<extra></extra>'
        )])
        
        fig.update_layout(
            title='Mapa Magnético del Área de Buceo',
            scene=dict(
                xaxis_title='Este-Oeste (m)',
                yaxis_title='Norte-Sur (m)',
                zaxis_title='Profundidad (m)'
            )
        )
        
        fig.show()


class SubmarineNavigator:
    """
    Navegador submarino completo
    Fusión de sensores: NV + IMU + Presión + GPS (cuando disponible)
    """
    
    def __init__(self, dt: float = 0.1, magnetic_map: Optional[MagneticMap] = None):
        self.dt = dt
        self.magnetic_map = magnetic_map or MagneticMap()
        
        # Filtro de Kalman Extendido
        # Estados: [x, y, z, vx, vy, vz, roll, pitch, yaw, bias_gx, bias_gy, bias_gz]
        self.ekf = ExtendedKalmanFilter(dim_x=12, dim_z=7)
        self._init_kalman()
        
        # Historial de navegación
        self.trajectory: List[NavigationState] = []
        self.raw_data: List[SensorData] = []
        
        # GPS de referencia (última posición conocida en superficie)
        self.last_gps_position: Optional[np.ndarray] = None
        self.gps_origin: Optional[Tuple[float, float]] = None  # (lat, lon) origen
        
        # Callbacks
        self.position_callback: Optional[Callable] = None
        
    def _init_kalman(self):
        """Inicializar matrices del filtro de Kalman"""
        dt = self.dt
        
        # Matriz de transición (modelo de velocidad constante)
        self.ekf.F = np.eye(12)
        self.ekf.F[0, 3] = dt  # x = x + vx*dt
        self.ekf.F[1, 4] = dt  # y = y + vy*dt
        self.ekf.F[2, 5] = dt  # z = z + vz*dt
        
        # Matriz de medición (observamos posición, orientación, profundidad)
        self.ekf.H = np.zeros((7, 12))
        self.ekf.H[0, 0] = 1  # x
        self.ekf.H[1, 1] = 1  # y
        self.ekf.H[2, 2] = 1  # z (from pressure)
        self.ekf.H[3, 6] = 1  # roll
        self.ekf.H[4, 7] = 1  # pitch
        self.ekf.H[5, 8] = 1  # yaw
        self.ekf.H[6, 2] = 1  # z (redundant, for weighting)
        
        # Covarianza inicial
        self.ekf.P *= 10
        
        # Ruido de medición
        self.ekf.R = np.diag([
            2.0,   # x (magnetic uncertainty)
            2.0,   # y (magnetic uncertainty)
            0.5,   # z (pressure is accurate)
            0.1,   # roll
            0.1,   # pitch
            0.2,   # yaw
            0.3    # z (redundant)
        ])
        
        # Ruido de proceso
        q_pos = Q_discrete_white_noise(dim=3, dt=dt, var=0.1)
        q_vel = Q_discrete_white_noise(dim=3, dt=dt, var=0.01)
        q_orient = np.eye(3) * 0.001
        q_bias = np.eye(3) * 0.0001
        
        self.ekf.Q = np.zeros((12, 12))
        self.ekf.Q[0:3, 0:3] = q_pos
        self.ekf.Q[3:6, 3:6] = q_vel
        self.ekf.Q[6:9, 6:9] = q_orient
        self.ekf.Q[9:12, 9:12] = q_bias
    
    def gps_to_local(self, lat: float, lon: float, alt: float) -> np.ndarray:
        """Convertir GPS (lat, lon, alt) a coordenadas locales (x, y, z)"""
        if self.gps_origin is None:
            self.gps_origin = (lat, lon)
            return np.array([0, 0, -alt])  # z negativo hacia abajo
        
        # Aproximación para distancias cortas (< 10 km)
        R_earth = 6371000  # metros
        lat0, lon0 = self.gps_origin
        
        x = R_earth * np.cos(np.radians(lat0)) * np.radians(lon - lon0)
        y = R_earth * np.radians(lat - lat0)
        z = -alt  # Negativo porque z aumenta hacia arriba
        
        return np.array([x, y, z])
    
    def update(self, data: SensorData) -> NavigationState:
        """
        Actualizar navegación con nuevos datos de sensores
        """
        # Guardar datos crudos
        self.raw_data.append(data)
        
        # Predicción con IMU
        self._predict_with_imu(data.gyro, data.accel)
        
        # Actualizar con magnetómetro (posición x, y)
        mag_position = self.magnetic_map.magnetic_to_position(data.magnetic_field)
        
        # Actualizar con presión (posición z)
        # Asumir 10m = 1 bar aproximadamente
        pressure_depth = data.pressure  # ya en metros
        
        # Actualizar con GPS si está disponible (superficie)
        at_surface = data.gps_position is not None
        if at_surface:
            gps_pos = self.gps_to_local(*data.gps_position)
            self.last_gps_position = gps_pos
            # GPS es muy preciso en x,y - actualizar fuertemente
            mag_position[0:2] = gps_pos[0:2]
        
        # Construir vector de medición
        orientation = self._get_orientation_from_imu(data.gyro)
        z = np.array([
            mag_position[0],
            mag_position[1],
            pressure_depth,
            orientation[0],
            orientation[1],
            orientation[2],
            pressure_depth  # Redundante para pesado
        ])
        
        # Actualizar Kalman
        self.ekf.update(z)
        
        # Crear estado de navegación
        state = NavigationState(
            timestamp=data.timestamp,
            position=self.ekf.x[0:3].copy(),
            velocity=self.ekf.x[3:6].copy(),
            orientation=self.ekf.x[6:9].copy(),
            magnetic_field=data.magnetic_field.copy(),
            confidence=self._calculate_confidence(),
            at_surface=at_surface
        )
        
        self.trajectory.append(state)
        
        # Llamar callback si existe
        if self.position_callback:
            self.position_callback(state)
        
        return state
    
    def _predict_with_imu(self, gyro: np.ndarray, accel: np.ndarray):
        """Predicción del estado usando IMU"""
        # Aquí iría la integración de las ecuaciones de movimiento
        # Simplificación: usar matriz F del Kalman
        self.ekf.predict()
    
    def _get_orientation_from_imu(self, gyro: np.ndarray) -> np.ndarray:
        """Obtener orientación integrando giroscopio"""
        if len(self.trajectory) > 0:
            last_orient = self.trajectory[-1].orientation
            # Integración simple de Euler
            new_orient = last_orient + (gyro - self.ekf.x[9:12]) * self.dt
        else:
            new_orient = np.zeros(3)
        
        return new_orient
    
    def _calculate_confidence(self) -> float:
        """Calcular nivel de confianza basado en covarianza"""
        # Menor traza de P = mayor confianza
        trace_p = np.trace(self.ekf.P[0:6, 0:6])  # Solo posición y velocidad
        confidence = np.exp(-trace_p / 100)
        return np.clip(confidence, 0, 1)
    
    def calibrate_mag_map(self, gps_points: List[Tuple]):
        """
        Calibrar mapa magnético usando puntos GPS de referencia
        gps_points: lista de (lat, lon, alt, Bx, By, Bz)
        """
        print(f"Calibrando mapa con {len(gps_points)} puntos GPS...")
        
        for lat, lon, alt, bx, by, bz in gps_points:
            position = self.gps_to_local(lat, lon, alt)
            magnetic = np.array([bx, by, bz])
            self.magnetic_map.add_calibration_point(position, magnetic)
        
        self.magnetic_map.save('magnetic_map.json')
        print(f"Mapa guardado: {len(self.magnetic_map.grid_points)} puntos")
    
    def get_current_position(self) -> Optional[NavigationState]:
        """Obtener posición actual"""
        if self.trajectory:
            return self.trajectory[-1]
        return None
    
    def save_dive_log(self, filename: str):
        """Guardar registro completo de la inmersión"""
        log = {
            'metadata': {
                'start_time': datetime.fromtimestamp(
                    self.trajectory[0].timestamp if self.trajectory else time.time()
                ).isoformat(),
                'duration': self.trajectory[-1].timestamp - self.trajectory[0].timestamp if len(self.trajectory) > 1 else 0,
                'total_points': len(self.trajectory),
                'gps_origin': self.gps_origin
            },
            'trajectory': [asdict(t) for t in self.trajectory],
            'raw_data': [
                {
                    'timestamp': d.timestamp,
                    'magnetic_field': d.magnetic_field.tolist(),
                    'gyro': d.gyro.tolist(),
                    'accel': d.accel.tolist(),
                    'pressure': d.pressure,
                    'temperature': d.temperature,
                    'gps_position': d.gps_position
                }
                for d in self.raw_data
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(log, f, indent=2)
        
        print(f"Registro de inmersión guardado: {filename}")
    
    def visualize_trajectory_3d(self, save_html: Optional[str] = None):
        """Visualizar trayectoria 3D interactiva"""
        if not self.trajectory:
            print("No hay datos de trayectoria")
            return
        
        positions = np.array([t.position for t in self.trajectory])
        confidences = [t.confidence for t in self.trajectory]
        
        # Crear figura
        fig = go.Figure()
        
        # Trayectoria principal
        fig.add_trace(go.Scatter3d(
            x=positions[:, 0],
            y=positions[:, 1],
            z=positions[:, 2],
            mode='lines+markers',
            marker=dict(
                size=4,
                color=confidences,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title='Confianza'),
                cmin=0,
                cmax=1
            ),
            line=dict(
                color='blue',
                width=3
            ),
            name='Trayectoria',
            hovertemplate='X:%{x:.1f}m<br>Y:%{y:.1f}m<br>Z:%{z:.1f}m<br>Conf:%{marker.color:.2f}<extra></extra>'
        ))
        
        # Marcar puntos GPS (superficie)
        gps_points = [(i, t) for i, t in enumerate(self.trajectory) if t.at_surface]
        if gps_points:
            gps_idx, gps_traj = zip(*gps_points)
            gps_pos = np.array([t.position for t in gps_traj])
            
            fig.add_trace(go.Scatter3d(
                x=gps_pos[:, 0],
                y=gps_pos[:, 1],
                z=gps_pos[:, 2],
                mode='markers',
                marker=dict(size=10, color='green', symbol='diamond'),
                name='GPS (Superficie)'
            ))
        
        # Inicio y fin
        fig.add_trace(go.Scatter3d(
            x=[positions[0, 0]],
            y=[positions[0, 1]],
            z=[positions[0, 2]],
            mode='markers+text',
            marker=dict(size=10, color='green'),
            text=['INICIO'],
            textposition='top center',
            name='Inicio'
        ))
        
        fig.add_trace(go.Scatter3d(
            x=[positions[-1, 0]],
            y=[positions[-1, 1]],
            z=[positions[-1, 2]],
            mode='markers+text',
            marker=dict(size=10, color='red'),
            text=['FIN'],
            textposition='top center',
            name='Fin'
        ))
        
        # Layout
        fig.update_layout(
            title='Trayectoria Submarina - Sistema de Navegación Cuántica',
            scene=dict(
                xaxis_title='Este-Oeste (m)',
                yaxis_title='Norte-Sur (m)',
                zaxis_title='Profundidad (m)',
                aspectmode='data',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
            ),
            width=1200,
            height=800,
            showlegend=True
        )
        
        if save_html:
            fig.write_html(save_html)
            print(f"Visualización guardada: {save_html}")
        
        fig.show()
    
    def create_dive_report(self) -> Dict:
        """Generar informe de la inmersión"""
        if not self.trajectory:
            return {}
        
        positions = np.array([t.position for t in self.trajectory])
        velocities = np.array([t.velocity for t in self.trajectory])
        
        # Distancia total
        distances = np.linalg.norm(np.diff(positions, axis=0), axis=1)
        total_distance = np.sum(distances)
        
        # Estadísticas de profundidad
        depths = -positions[:, 2]  # Convertir a positivo
        max_depth = np.max(depths)
        avg_depth = np.mean(depths)
        
        # Velocidad
        speeds = np.linalg.norm(velocities, axis=1)
        avg_speed = np.mean(speeds)
        max_speed = np.max(speeds)
        
        # Duración
        duration = self.trajectory[-1].timestamp - self.trajectory[0].timestamp
        
        # Desviación estándar (precisión estimada)
        position_std = np.std(positions, axis=0)
        
        report = {
            'duracion_segundos': duration,
            'duracion_minutos': duration / 60,
            'distancia_total_m': total_distance,
            'profundidad_max_m': max_depth,
            'profundidad_media_m': avg_depth,
            'velocidad_media_ms': avg_speed,
            'velocidad_max_ms': max_speed,
            'precision_estimada_m': np.mean(position_std),
            'puntos_gps': sum(1 for t in self.trajectory if t.at_surface),
            'confianza_media': np.mean([t.confidence for t in self.trajectory])
        }
        
        return report


class SensorInterface:
    """
    Interfaz para comunicación con hardware de sensores
    """
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.data_callback: Optional[Callable] = None
        self.thread: Optional[threading.Thread] = None
    
    def connect(self) -> bool:
        """Conectar al hardware"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Esperar inicialización
            self.running = True
            self.thread = threading.Thread(target=self._read_loop)
            self.thread.start()
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False
    
    def disconnect(self):
        """Desconectar del hardware"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial:
            self.serial.close()
    
    def _read_loop(self):
        """Bucle de lectura en segundo plano"""
        while self.running:
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode().strip()
                    data = self._parse_line(line)
                    if data and self.data_callback:
                        self.data_callback(data)
            except Exception as e:
                print(f"Error lectura: {e}")
    
    def _parse_line(self, line: str) -> Optional[SensorData]:
        """Parsear línea de datos del sensor"""
        try:
            # Formato esperado: JSON con campos del sensor
            if line.startswith('{'):
                j = json.loads(line)
                return SensorData(
                    timestamp=time.time(),
                    magnetic_field=np.array([
                        j.get('bx', 0),
                        j.get('by', 0),
                        j.get('bz', 0)
                    ]),
                    gyro=np.array([
                        j.get('gx', 0),
                        j.get('gy', 0),
                        j.get('gz', 0)
                    ]),
                    accel=np.array([
                        j.get('ax', 0),
                        j.get('ay', 0),
                        j.get('az', 0)
                    ]),
                    pressure=j.get('depth', 0),
                    temperature=j.get('temp', 0),
                    gps_position=j.get('gps') if 'gps' in j else None
                )
        except:
            pass
        return None
    
    def send_command(self, cmd: str):
        """Enviar comando al hardware"""
        if self.serial:
            self.serial.write(f"{cmd}\n".encode())


def simulate_dive(navigator: SubmarineNavigator, duration: float = 120):
    """Simular una inmersión para pruebas"""
    print(f"Simulando inmersión de {duration}s...")
    
    start_time = time.time()
    step = 0
    
    while time.time() - start_time < duration:
        t = time.time() - start_time
        
        # Simular trayectoria: círculo descendente
        x = 20 * np.cos(0.05 * t)
        y = 20 * np.sin(0.05 * t)
        z = -0.5 * t  # Descendiendo 0.5 m/s
        
        # Campo magnético (gradiente simple)
        Bx = 30e-6 + x * 1e-9 + np.random.normal(0, 1e-9)
        By = 5e-6 + y * 1e-9 + np.random.normal(0, 1e-9)
        Bz = 40e-6 + z * 1e-9 + np.random.normal(0, 1e-9)
        
        # IMU
        gyro = np.array([0.01, 0.02, 0.05]) + np.random.normal(0, 0.001, 3)
        accel = np.array([0, 0, -9.81]) + np.random.normal(0, 0.01, 3)
        
        # Presión (profundidad)
        pressure = abs(z) + np.random.normal(0, 0.1)
        
        # GPS solo en superficie (z > -1m)
        gps = None
        if z > -1:
            gps = (41.3851 + x/111000, 2.1734 + y/111000, 0)
        
        data = SensorData(
            timestamp=time.time(),
            magnetic_field=np.array([Bx, By, Bz]),
            gyro=gyro,
            accel=accel,
            pressure=pressure,
            temperature=25.0,
            gps_position=gps
        )
        
        state = navigator.update(data)
        
        if step % 50 == 0:
            print(f"t={t:.1f}s: Pos=({state.position[0]:.1f}, {state.position[1]:.1f}, {state.position[2]:.1f}), "
                  f"Conf={state.confidence:.2f}, GPS={state.at_surface}")
        
        step += 1
        time.sleep(0.1)
    
    print("Simulación completada")


def main():
    parser = argparse.ArgumentParser(description='Sistema de Mapeo Submarino')
    parser.add_argument('--mode', choices=['real', 'simulate'], default='simulate',
                       help='Modo de operación')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Puerto Serial')
    parser.add_argument('--duration', type=float, default=120, help='Duración (s)')
    parser.add_argument('--map', help='Archivo de mapa magnético')
    parser.add_argument('--output', default='dive_log.json', help='Archivo de salida')
    
    args = parser.parse_args()
    
    # Cargar mapa magnético si existe
    mag_map = MagneticMap(args.map) if args.map else MagneticMap()
    
    # Crear navegador
    navigator = SubmarineNavigator(dt=0.1, magnetic_map=mag_map)
    
    if args.mode == 'real':
        # Modo real con hardware
        interface = SensorInterface(port=args.port)
        
        if not interface.connect():
            print("No se pudo conectar al hardware")
            return
        
        # Configurar callback
        interface.data_callback = navigator.update
        
        print("Navegación iniciada. Presiona Ctrl+C para detener.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDeteniendo...")
        finally:
            interface.disconnect()
    
    else:
        # Modo simulación
        simulate_dive(navigator, args.duration)
    
    # Guardar resultados
    navigator.save_dive_log(args.output)
    
    # Generar informe
    report = navigator.create_dive_report()
    print("\n=== INFORME DE INMERSIÓN ===")
    for key, value in report.items():
        print(f"{key}: {value}")
    
    # Visualizar
    navigator.visualize_trajectory_3d('trajectory.html')
    
    if mag_map.grid_points:
        mag_map.visualize()


if __name__ == '__main__':
    main()
