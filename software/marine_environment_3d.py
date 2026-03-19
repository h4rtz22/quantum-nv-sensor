#!/usr/bin/env python3
"""
Entorno Marino 3D - Integración de trayectoria con mapa del fondo marino
Visualización completa del espacio submarino

Uso:
    python3 marine_environment_3d.py --bathymetry data/bathymetry.csv --trajectory dive_log.json
"""

import numpy as np
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


@dataclass
class BathymetryPoint:
    """Punto de batimetría"""
    x: float  # metros
    y: float
    depth: float  # positivo hacia abajo
    

@dataclass
class UnderwaterObject:
    """Objeto submarino (pecios, arrecifes, etc.)"""
    name: str
    position: Tuple[float, float, float]  # x, y, z
    size: Tuple[float, float, float]      # width, height, depth
    object_type: str  # 'wreck', 'reef', 'cave', 'marker'
    description: str


class MarineEnvironment3D:
    """
    Entorno marino 3D completo
    Incluye batimetría, objetos, y trayectoria del buceador
    """
    
    def __init__(self, origin_lat: float = 41.3851, origin_lon: float = 2.1734):
        self.origin = (origin_lat, origin_lon)
        self.bathymetry: List[BathymetryPoint] = []
        self.objects: List[UnderwaterObject] = []
        self.trajectory: Optional[np.ndarray] = None
        self.currents: Optional[Dict] = None
        
    def load_bathymetry_from_csv(self, filename: str):
        """Cargar datos de batimetría desde CSV"""
        import csv
        
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.bathymetry.append(BathymetryPoint(
                    x=float(row['x']),
                    y=float(row['y']),
                    depth=float(row['depth'])
                ))
        
        print(f"Batimetría cargada: {len(self.bathymetry)} puntos")
    
    def load_bathymetry_from_multibeam(self, filename: str):
        """Cargar datos de sonar multihaz"""
        # Formato típico: x, y, z, intensity, quality
        data = np.loadtxt(filename, delimiter=',')
        
        for row in data:
            self.bathymetry.append(BathymetryPoint(
                x=row[0],
                y=row[1],
                depth=abs(row[2])  # Asegurar positivo
            ))
        
        print(f"Datos multihaz cargados: {len(self.bathymetry)} puntos")
    
    def generate_synthetic_bathymetry(self, x_range: Tuple[float, float] = (-100, 100),
                                             y_range: Tuple[float, float] = (-100, 100),
                                             resolution: float = 5.0):
        """Generar batimetría sintética para pruebas"""
        x = np.arange(x_range[0], x_range[1], resolution)
        y = np.arange(y_range[0], y_range[1], resolution)
        X, Y = np.meshgrid(x, y)
        
        # Generar fondo marino realista con ruido Perlin + estructuras
        Z = self._generate_seafloor(X, Y)
        
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                self.bathymetry.append(BathymetryPoint(
                    x=X[i, j],
                    y=Y[i, j],
                    depth=Z[i, j]
                ))
        
        print(f"Batimetría sintética generada: {len(self.bathymetry)} puntos")
    
    def _generate_seafloor(self, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
        """Generar fondo marino realista"""
        # Combinación de ondas sinusoidales (simula dunas, montes)
        Z = (
            20 +  # Profundidad base
            10 * np.sin(X / 30) * np.cos(Y / 30) +  # Grandes estructuras
            5 * np.sin(X / 10) * np.sin(Y / 10) +   # Detalles pequeños
            3 * np.random.randn(*X.shape)            # Ruido
        )
        
        # Añadir cañón submarino
        canyon_center = np.array([0, 0])
        dist_to_canyon = np.sqrt((X - canyon_center[0])**2 + (Y - canyon_center[1])**2)
        canyon_depth = 30 * np.exp(-dist_to_canyon / 20)
        Z += canyon_depth
        
        return np.maximum(Z, 5)  # Mínimo 5m de profundidad
    
    def add_object(self, obj: UnderwaterObject):
        """Añadir objeto submarino al entorno"""
        self.objects.append(obj)
    
    def add_default_objects(self):
        """Añadir objetos de ejemplo"""
        # Pecio
        self.add_object(UnderwaterObject(
            name="Pecio SS Barcelona",
            position=(25, 15, -35),
            size=(15, 8, 5),
            object_type="wreck",
            description="Barco de carga hundido en 1942"
        ))
        
        # Arrecife artificial
        self.add_object(UnderwaterObject(
            name="Arrecife Artificial",
            position=(-30, -20, -18),
            size=(20, 12, 8),
            object_type="reef",
            description="Estructura de hormigón colonizada por coral"
        ))
        
        # Cueva submarina
        self.add_object(UnderwaterObject(
            name="Cueva del Toro",
            position=(10, -40, -25),
            size=(8, 5, 12),
            object_type="cave",
            description="Sistema de cuevas submarinas"
        ))
        
        # Boya de referencia
        self.add_object(UnderwaterObject(
            name="Boya de Referencia A",
            position=(0, 0, 0),
            size=(2, 2, 5),
            object_type="marker",
            description="Punto de referencia GPS"
        ))
    
    def load_trajectory(self, filename: str):
        """Cargar trayectoria del buceador"""
        with open(filename) as f:
            data = json.load(f)
        
        trajectory_data = data.get('trajectory', [])
        self.trajectory = np.array([t['position'] for t in trajectory_data])
        
        print(f"Trayectoria cargada: {len(self.trajectory)} puntos")
    
    def create_3d_scene(self, save_html: Optional[str] = None) -> go.Figure:
        """Crear escena 3D completa"""
        fig = go.Figure()
        
        # 1. Fondo marino (superficie 3D)
        if self.bathymetry:
            self._add_seafloor_surface(fig)
        
        # 2. Objetos submarinos
        self._add_underwater_objects(fig)
        
        # 3. Trayectoria del buceador
        if self.trajectory is not None:
            self._add_diver_trajectory(fig)
        
        # 4. Superficie del agua
        self._add_water_surface(fig)
        
        # 5. Configuración de la escena
        self._configure_scene(fig)
        
        if save_html:
            fig.write_html(save_html)
            print(f"Escena 3D guardada: {save_html}")
        
        return fig
    
    def _add_seafloor_surface(self, fig: go.Figure):
        """Añadir superficie del fondo marino"""
        points = np.array([[b.x, b.y, b.depth] for b in self.bathymetry])
        
        # Crear grilla regular para superficie
        x_unique = np.unique(points[:, 0])
        y_unique = np.unique(points[:, 1])
        
        if len(x_unique) > 1 and len(y_unique) > 1:
            X, Y = np.meshgrid(x_unique, y_unique)
            Z = np.zeros_like(X)
            
            # Interpolar valores Z
            from scipy.interpolate import griddata
            Z = griddata(
                points[:, 0:2],
                points[:, 2],
                (X, Y),
                method='linear',
                fill_value=np.mean(points[:, 2])
            )
            
            # Superficie del fondo
            fig.add_trace(go.Surface(
                x=X,
                y=Y,
                z=-Z,  # Negativo para que profundidad sea hacia abajo
                colorscale='Earth',
                showscale=True,
                colorbar=dict(title='Profundidad (m)'),
                name='Fondo Marino',
                opacity=0.9,
                hovertemplate='X:%{x:.1f}<br>Y:%{y:.1f}<br>Prof:%{z:.1f}m<extra></extra>'
            ))
    
    def _add_underwater_objects(self, fig: go.Figure):
        """Añadir objetos submarinos como meshes 3D"""
        colors = {
            'wreck': '#8B4513',      # Marrón (óxido)
            'reef': '#FF6B6B',       # Coral
            'cave': '#4A4A4A',       # Gris oscuro
            'marker': '#FFD93D'      # Amarillo
        }
        
        for obj in self.objects:
            x, y, z = obj.position
            w, h, d = obj.size
            color = colors.get(obj.object_type, '#888888')
            
            # Crear caja 3D para el objeto
            fig.add_trace(self._create_3d_box(x, y, z, w, h, d, color, obj.name, obj.description))
    
    def _create_3d_box(self, x, y, z, w, h, d, color, name, description):
        """Crear mesh 3D de una caja"""
        # Vértices de la caja
        vertices = np.array([
            [x-w/2, y-h/2, z],      # 0: abajo-izq-frente
            [x+w/2, y-h/2, z],      # 1: abajo-der-frente
            [x+w/2, y+h/2, z],      # 2: abajo-der-atrás
            [x-w/2, y+h/2, z],      # 3: abajo-izq-atrás
            [x-w/2, y-h/2, z+d],    # 4: arriba-izq-frente
            [x+w/2, y-h/2, z+d],    # 5: arriba-der-frente
            [x+w/2, y+h/2, z+d],    # 6: arriba-der-atrás
            [x-w/2, y+h/2, z+d],    # 7: arriba-izq-atrás
        ])
        
        # Caras de la caja (triángulos)
        faces = [
            [0, 1, 2], [0, 2, 3],  # abajo
            [4, 5, 6], [4, 6, 7],  # arriba
            [0, 1, 5], [0, 5, 4],  # frente
            [2, 3, 7], [2, 7, 6],  # atrás
            [0, 3, 7], [0, 7, 4],  # izq
            [1, 2, 6], [1, 6, 5],  # der
        ]
        
        # Z debe ser negativo (profundidad)
        vertices[:, 2] = -vertices[:, 2]
        
        return go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=[f[0] for f in faces],
            j=[f[1] for f in faces],
            k=[f[2] for f in faces],
            color=color,
            opacity=0.8,
            name=name,
            hovertemplate=f'<b>{name}</b><br>{description}<extra></extra>'
        )
    
    def _add_diver_trajectory(self, fig: go.Figure):
        """Añadir trayectoria del buceador"""
        traj = self.trajectory
        
        # Línea de trayectoria
        fig.add_trace(go.Scatter3d(
            x=traj[:, 0],
            y=traj[:, 1],
            z=-traj[:, 2],  # Negativo para profundidad
            mode='lines+markers',
            line=dict(
                color='cyan',
                width=6,
                colorscale='Viridis'
            ),
            marker=dict(
                size=3,
                color=np.arange(len(traj)),
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Tiempo', x=0.9)
            ),
            name='Buceador',
            hovertemplate='X:%{x:.1f}<br>Y:%{y:.1f}<br>Z:%{z:.1f}m<extra></extra>'
        ))
        
        # Punto de inicio
        fig.add_trace(go.Scatter3d(
            x=[traj[0, 0]],
            y=[traj[0, 1]],
            z=[-traj[0, 2]],
            mode='markers+text',
            marker=dict(size=10, color='green', symbol='diamond'),
            text=['INICIO'],
            textposition='top center',
            name='Inicio'
        ))
        
        # Punto final
        fig.add_trace(go.Scatter3d(
            x=[traj[-1, 0]],
            y=[traj[-1, 1]],
            z=[-traj[-1, 2]],
            mode='markers+text',
            marker=dict(size=10, color='red', symbol='diamond'),
            text=['FIN'],
            textposition='top center',
            name='Fin'
        ))
    
    def _add_water_surface(self, fig: go.Figure):
        """Añadir superficie del agua (plano transparente en z=0)"""
        if not self.bathymetry:
            return
        
        x_range = [min(b.x for b in self.bathymetry), max(b.x for b in self.bathymetry)]
        y_range = [min(b.y for b in self.bathymetry), max(b.y for b in self.bathymetry)]
        
        fig.add_trace(go.Surface(
            x=np.linspace(x_range[0], x_range[1], 10),
            y=np.linspace(y_range[0], y_range[1], 10),
            z=np.zeros((10, 10)),
            colorscale=[[0, '#0066CC'], [1, '#0066CC']],
            showscale=False,
            opacity=0.3,
            name='Superficie',
            hoverinfo='skip'
        ))
    
    def _configure_scene(self, fig: go.Figure):
        """Configurar aspecto de la escena"""
        fig.update_layout(
            title=dict(
                text='Entorno Marino 3D - Navegación Cuántica',
                x=0.5,
                font=dict(size=20)
            ),
            scene=dict(
                xaxis_title='Este-Oeste (m)',
                yaxis_title='Norte-Sur (m)',
                zaxis_title='Profundidad (m)',
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=0.5),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=0.8),
                    center=dict(x=0, y=0, z=-0.2)
                ),
                bgcolor='#001133'  # Fondo azul oscuro (agua profunda)
            ),
            width=1400,
            height=900,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
    
    def create_cross_section(self, x_slice: Optional[float] = None,
                            y_slice: Optional[float] = None,
                            save_html: Optional[str] = None):
        """Crear vista de corte transversal"""
        if not self.bathymetry:
            print("No hay datos de batimetría")
            return
        
        points = np.array([[b.x, b.y, b.depth] for b in self.bathymetry])
        
        # Seleccionar corte
        if x_slice is not None:
            # Corte en X (vista lateral Y-Z)
            idx = np.argmin(np.abs(points[:, 0] - x_slice))
            x_val = points[idx, 0]
            slice_points = points[np.abs(points[:, 0] - x_val) < 5]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=slice_points[:, 1],
                y=-slice_points[:, 2],
                mode='markers',
                name='Fondo marino'
            ))
            
            if self.trajectory is not None:
                traj_slice = self.trajectory[np.abs(self.trajectory[:, 0] - x_val) < 5]
                fig.add_trace(go.Scatter(
                    x=traj_slice[:, 1],
                    y=-traj_slice[:, 2],
                    mode='lines+markers',
                    name='Trayectoria'
                ))
            
            fig.update_layout(
                title=f'Corte transversal en X={x_val:.1f}m',
                xaxis_title='Y (m)',
                yaxis_title='Profundidad (m)'
            )
        
        else:
            print("Especificar x_slice o y_slice")
            return
        
        if save_html:
            fig.write_html(save_html)
        
        fig.show()
    
    def calculate_distance_to_seafloor(self) -> np.ndarray:
        """Calcular distancia del buceador al fondo en cada punto"""
        if self.trajectory is None or not self.bathymetry:
            return np.array([])
        
        distances = []
        for pos in self.trajectory:
            # Encontrar punto de fondo más cercano
            bath_points = np.array([[b.x, b.y, b.depth] for b in self.bathymetry])
            dx = bath_points[:, 0] - pos[0]
            dy = bath_points[:, 1] - pos[1]
            dist_2d = np.sqrt(dx**2 + dy**2)
            nearest_idx = np.argmin(dist_2d)
            
            # Distancia vertical al fondo
            seafloor_depth = bath_points[nearest_idx, 2]
            diver_depth = abs(pos[2])
            distance = seafloor_depth - diver_depth
            distances.append(distance)
        
        return np.array(distances)
    
    def safety_analysis(self) -> Dict:
        """Análisis de seguridad de la inmersión"""
        if self.trajectory is None:
            return {}
        
        distances = self.calculate_distance_to_seafloor()
        
        analysis = {
            'min_distance_to_seafloor': np.min(distances),
            'avg_distance_to_seafloor': np.mean(distances),
            'max_depth': np.max(np.abs(self.trajectory[:, 2])),
            'total_distance_swum': np.sum(np.linalg.norm(np.diff(self.trajectory, axis=0), axis=1)),
            'safety_warnings': []
        }
        
        # Alertas de seguridad
        if analysis['min_distance_to_seafloor'] < 2:
            analysis['safety_warnings'].append('⚠️ Riesgo de colisión con el fondo')
        
        if analysis['max_depth'] > 40:
            analysis['safety_warnings'].append('⚠️ Profundidad > 40m - revisar tiempos de descompresión')
        
        return analysis


def main():
    parser = argparse.ArgumentParser(description='Entorno Marino 3D')
    parser.add_argument('--bathymetry', help='Archivo CSV de batimetría')
    parser.add_argument('--trajectory', help='Archivo JSON de trayectoria')
    parser.add_argument('--synthetic', action='store_true', help='Generar datos sintéticos')
    parser.add_argument('--output', default='marine_environment.html', help='Archivo HTML salida')
    
    args = parser.parse_args()
    
    # Crear entorno
    env = MarineEnvironment3D()
    
    # Cargar o generar batimetría
    if args.bathymetry:
        env.load_bathymetry_from_csv(args.bathymetry)
    elif args.synthetic:
        env.generate_synthetic_bathymetry()
    else:
        print("Usando batimetría sintética por defecto")
        env.generate_synthetic_bathymetry()
    
    # Añadir objetos
    env.add_default_objects()
    
    # Cargar trayectoria si existe
    if args.trajectory and Path(args.trajectory).exists():
        env.load_trajectory(args.trajectory)
    
    # Crear visualización 3D
    fig = env.create_3d_scene(save_html=args.output)
    fig.show()
    
    # Análisis de seguridad
    if env.trajectory is not None:
        safety = env.safety_analysis()
        print("\n=== ANÁLISIS DE SEGURIDAD ===")
        for key, value in safety.items():
            print(f"{key}: {value}")
    
    print(f"\nVisualización guardada en: {args.output}")


if __name__ == '__main__':
    main()
