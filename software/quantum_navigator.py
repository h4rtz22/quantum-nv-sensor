#!/usr/bin/env python3
"""
Sistema de navegación cuántica con sensor NV
Fusión de sensores + Mapeo 3D

Uso:
    python3 quantum_navigator.py --input nv_data.json
    python3 quantum_navigator.py --simulate
"""

import numpy as np
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse


class QuantumNavigator:
    """
    Navegador cuántico con fusión de sensores
    Estados: [x, y, z, vx, vy, vz, roll, pitch, yaw]
    """
    
    def __init__(self, dt: float = 0.1):
        self.dt = dt
        
        # Filtro de Kalman 9 estados
        self.kf = KalmanFilter(dim_x=9, dim_z=6)
        
        # Matriz de transición (modelo de velocidad constante)
        self._build_transition_matrix()
        
        # Matriz de medición (observamos pos y orientación)
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Covarianzas iniciales
        self.kf.P *= 10
        self.kf.R = np.diag([1, 1, 2, 0.1, 0.1, 0.1])  # Ruido medición
        
        # Ruido de proceso
        self._build_process_noise()
        
        # Historial de trayectoria
        self.trajectory: List[Dict] = []
        self.magnetic_map = None  # Mapa magnético del área
        
    def _build_transition_matrix(self):
        """Construir matriz de transición F"""
        dt = self.dt
        self.kf.F = np.array([
            [1, 0, 0, dt, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, dt, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, dt, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 1]
        ])
    
    def _build_process_noise(self):
        """Construir matriz de ruido de proceso Q"""
        q = Q_discrete_white_noise(dim=3, dt=self.dt, var=0.1)
        self.kf.Q = np.zeros((9, 9))
        self.kf.Q[:3, :3] = q
        self.kf.Q[3:6, 3:6] = q * 0.1
    
    def load_magnetic_map(self, map_file: str):
        """Cargar mapa magnético del área de buceo"""
        with open(map_file) as f:
            self.magnetic_map = json.load(f)
        print(f"Mapa magnético cargado: {len(self.magnetic_map)} puntos")
    
    def magnetic_to_position(self, mag_field: np.ndarray) -> np.ndarray:
        """
        Convertir lectura magnética a posición estimada
        Usa mapa magnético si está disponible, o modelo simple
        """
        if self.magnetic_map:
            # Buscar punto más cercano en el mapa
            # (Implementación de interpolación)
            return self._interpolate_magnetic(mag_field)
        else:
            # Modelo simple: gradiente lineal
            # En la realidad, esto requiere calibración del área
            scale = np.array([1000, 1000, 500])  # m/T (ejemplo)
            return mag_field * scale
    
    def _interpolate_magnetic(self, mag_field: np.ndarray) -> np.ndarray:
        """Interpolación en mapa magnético"""
        # Implementar interpolación 3D
        # Por ahora, retornar valor más cercano
        return np.zeros(3)  # Placeholder
    
    def integrate_gyro(self, gyro: np.ndarray) -> np.ndarray:
        """Integrar giroscopio para obtener orientación"""
        if len(self.trajectory) > 0:
            last_orient = np.array(self.trajectory[-1]['orientation'])
            # Integración simple de Euler
            new_orient = last_orient + gyro * self.dt
        else:
            new_orient = np.zeros(3)
        
        return new_orient
    
    def update(self, mag_field: np.ndarray, gyro: np.ndarray, 
               accel: np.ndarray, dt: Optional[float] = None) -> np.ndarray:
        """
        Actualizar estimación con nuevas mediciones
        
        Args:
            mag_field: [Bx, By, Bz] en Tesla
            gyro: [wx, wy, wz] en rad/s
            accel: [ax, ay, az] en m/s²
            dt: Intervalo de tiempo (opcional)
        
        Returns:
            Posición estimada [x, y, z]
        """
        if dt and dt != self.dt:
            self.dt = dt
            self._build_transition_matrix()
        
        # Predicción
        self.kf.predict()
        
        # Calcular posición estimada desde campo magnético
        pos_estimate = self.magnetic_to_position(mag_field)
        
        # Calcular orientación desde giroscopio
        orientation = self.integrate_gyro(gyro)
        
        # Actualizar con medición
        z = np.concatenate([pos_estimate, orientation])
        self.kf.update(z)
        
        # Guardar trayectoria
        state = self.kf.x.copy()
        self.trajectory.append({
            'timestamp': datetime.now().isoformat(),
            'position': state[:3].tolist(),
            'velocity': state[3:6].tolist(),
            'orientation': state[6:9].tolist(),
            'magnetic_field': mag_field.tolist(),
            'gyro': gyro.tolist(),
            'accel': accel.tolist()
        })
        
        return state[:3]
    
    def save_trajectory(self, filename: str):
        """Guardar trayectoria a archivo JSON"""
        output = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'points': len(self.trajectory),
                'dt': self.dt
            },
            'trajectory': self.trajectory
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Trayectoria guardada en {filename}")
    
    def load_trajectory(self, filename: str):
        """Cargar trayectoria desde archivo"""
        with open(filename) as f:
            data = json.load(f)
            self.trajectory = data['trajectory']
        print(f"Trayectoria cargada: {len(self.trajectory)} puntos")
    
    def plot_3d_trajectory(self, save_html: Optional[str] = None):
        """Visualizar trayectoria en 3D con Plotly"""
        if not self.trajectory:
            print("No hay datos de trayectoria")
            return
        
        positions = np.array([t['position'] for t in self.trajectory])
        
        fig = go.Figure(data=[go.Scatter3d(
            x=positions[:, 0],
            y=positions[:, 1],
            z=positions[:, 2],
            mode='lines+markers',
            marker=dict(
                size=4,
                color=positions[:, 2],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Profundidad (m)')
            ),
            line=dict(
                width=4,
                color=positions[:, 2],
                colorscale='Viridis'
            ),
            text=[f"T:{i}<br>Z:{p[2]:.1f}m" for i, p in enumerate(positions)],
            hovertemplate='%{text}<br>X:%{x:.1f}<br>Y:%{y:.1f}<extra></extra>'
        )])
        
        # Añadir punto de inicio y fin
        fig.add_trace(go.Scatter3d(
            x=[positions[0, 0]], y=[positions[0, 1]], z=[positions[0, 2]],
            mode='markers', marker=dict(size=8, color='green'),
            name='Inicio'
        ))
        fig.add_trace(go.Scatter3d(
            x=[positions[-1, 0]], y=[positions[-1, 1]], z=[positions[-1, 2]],
            mode='markers', marker=dict(size=8, color='red'),
            name='Fin'
        ))
        
        fig.update_layout(
            title='Trayectoria Submarinista - Sensor Cuántico NV',
            scene=dict(
                xaxis_title='Este-Oeste (m)',
                yaxis_title='Norte-Sur (m)',
                zaxis_title='Profundidad (m)',
                aspectmode='data',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
            ),
            width=1000,
            height=800
        )
        
        if save_html:
            fig.write_html(save_html)
            print(f"Visualización guardada en {save_html}")
        
        fig.show()
    
    def plot_dashboard(self, save_html: Optional[str] = None):
        """Dashboard completo con múltiples gráficas"""
        if not self.trajectory:
            print("No hay datos")
            return
        
        positions = np.array([t['position'] for t in self.trajectory])
        velocities = np.array([t['velocity'] for t in self.trajectory])
        mag_fields = np.array([t['magnetic_field'] for t in self.trajectory])
        
        fig = make_subplots(
            rows=3, cols=2,
            specs=[
                [{'type': 'scatter3d', 'colspan': 2}, None],
                [{'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'scatter', 'colspan': 2}, None]
            ],
            subplot_titles=(
                'Trayectoria 3D', '',
                'Velocidad', 'Campo Magnético',
                'Profundidad vs Tiempo', ''
            ),
            vertical_spacing=0.1
        )
        
        # Trayectoria 3D
        fig.add_trace(go.Scatter3d(
            x=positions[:, 0], y=positions[:, 1], z=positions[:, 2],
            mode='lines+markers', marker=dict(size=3, color='blue'),
            name='Trayectoria'
        ), row=1, col=1)
        
        # Velocidad
        speed = np.linalg.norm(velocities, axis=1)
        fig.add_trace(go.Scatter(
            y=speed, mode='lines', name='Velocidad',
            line=dict(color='green')
        ), row=2, col=1)
        
        # Campo magnético (componente Z)
        fig.add_trace(go.Scatter(
            y=mag_fields[:, 2] * 1e6, mode='lines', name='Bz',
            line=dict(color='red')
        ), row=2, col=2)
        
        # Profundidad
        fig.add_trace(go.Scatter(
            y=positions[:, 2], mode='lines', name='Profundidad',
            line=dict(color='purple')
        ), row=3, col=1)
        
        fig.update_layout(height=1200, showlegend=False)
        
        if save_html:
            fig.write_html(save_html)
            print(f"Dashboard guardado en {save_html}")
        
        fig.show()
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas de la trayectoria"""
        if not self.trajectory:
            return {}
        
        positions = np.array([t['position'] for t in self.trajectory])
        velocities = np.array([t['velocity'] for t in self.trajectory])
        
        # Distancia total recorrida
        distances = np.linalg.norm(np.diff(positions, axis=0), axis=1)
        total_distance = np.sum(distances)
        
        # Profundidad máxima
        max_depth = np.min(positions[:, 2])  # Z es negativo hacia abajo
        
        # Velocidad media y máxima
        speeds = np.linalg.norm(velocities, axis=1)
        avg_speed = np.mean(speeds)
        max_speed = np.max(speeds)
        
        return {
            'total_points': len(self.trajectory),
            'total_distance_m': total_distance,
            'max_depth_m': abs(max_depth),
            'avg_speed_ms': avg_speed,
            'max_speed_ms': max_speed,
            'duration_s': len(self.trajectory) * self.dt
        }


def simulate_dive(navigator: QuantumNavigator, duration: float = 60):
    """Simular una inmersión para pruebas"""
    print(f"Simulando inmersión de {duration}s...")
    
    steps = int(duration / navigator.dt)
    
    for i in range(steps):
        # Simular movimiento circular descendente
        t = i * navigator.dt
        
        # Posición simulada
        x = 10 * np.cos(0.1 * t)
        y = 10 * np.sin(0.1 * t)
        z = -0.5 * t  # Descendiendo 0.5 m/s
        
        # Campo magnético simulado (gradiente simple)
        Bx = 30e-6 + x * 1e-9
        By = 5e-6 + y * 1e-9
        Bz = 40e-6 + z * 1e-9
        
        # Giroscopio simulado
        gyro = np.array([0.01, 0.02, 0.1])  # Rotación constante
        
        # Acelerómetro (gravedad + movimiento)
        accel = np.array([0, 0, -9.81])
        
        # Actualizar navegador
        mag_field = np.array([Bx, By, Bz])
        pos = navigator.update(mag_field, gyro, accel)
        
        if i % 50 == 0:
            print(f"t={t:.1f}s: Pos=({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    print("Simulación completada")


def main():
    parser = argparse.ArgumentParser(description='Navegador Cuántico NV')
    parser.add_argument('--input', help='Archivo de trayectoria JSON')
    parser.add_argument('--output', default='trayectoria.html', help='Archivo HTML salida')
    parser.add_argument('--simulate', action='store_true', help='Simular inmersión')
    parser.add_argument('--duration', type=float, default=60, help='Duración simulación')
    parser.add_argument('--dt', type=float, default=0.1, help='Intervalo de tiempo')
    parser.add_argument('--dashboard', action='store_true', help='Mostrar dashboard completo')
    
    args = parser.parse_args()
    
    navigator = QuantumNavigator(dt=args.dt)
    
    if args.input:
        # Cargar datos existentes
        navigator.load_trajectory(args.input)
    elif args.simulate:
        # Simular nueva inmersión
        simulate_dive(navigator, args.duration)
        navigator.save_trajectory('simulated_dive.json')
    else:
        print("Usar --input para cargar datos o --simulate para simular")
        return
    
    # Mostrar estadísticas
    stats = navigator.get_statistics()
    print("\nEstadísticas:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Visualizar
    if args.dashboard:
        navigator.plot_dashboard(args.output)
    else:
        navigator.plot_3d_trajectory(args.output)


if __name__ == '__main__':
    main()
