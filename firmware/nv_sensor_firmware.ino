/*
 * Firmware para Sensor NV - Control cuántico de diamante
 * Compatible: Arduino Due / Raspberry Pi Pico
 * 
 * Funciones:
 * - Control láser 532nm (ON/OFF/TTL)
 * - Barrido de frecuencia microondas (ODMR)
 * - Lectura ADC de fluorescencia
 * - Cálculo de campo magnético
 * - Comunicación Serial (JSON)
 */

#include <SPI.h>
#include <Wire.h>
#include <ADS1115.h>

// ==================== CONFIGURACIÓN DE PINES ====================
const int LASER_PIN = 17;        // Control láser (TTL)
const int LASER_PWM = 18;        // Ajuste potencia láser (opcional)
const int MW_LE_PIN = 23;        // Latch Enable ADF4351
const int MW_DATA_PIN = 27;      // SPI Data ADF4351
const int MW_CLK_PIN = 22;       // SPI Clock ADF4351
const int LED_STATUS = 25;       // LED indicador

// ==================== CONSTANTES FÍSICAS ====================
const float MW_FREQ_CENTER = 2.87e9;    // Frecuencia cero campo [Hz]
const float MW_FREQ_SPAN = 100e6;        // Span de barrido [Hz]
const int MW_STEPS = 100;                // Pasos de barrido
const float GAMMA_E = 28.024e9;          // Factor giromagnético electrón [Hz/T]
const float TESLA_TO_GAUSS = 1e4;        // Conversión

// ==================== VARIABLES GLOBALES ====================
ADS1115 adc;
float currentFreq = MW_FREQ_CENTER;
float calibrationOffset = 0.0;
float calibrationScale = 1.0;

// Estructura para datos ODMR
struct ODMRData {
  float frequency;
  float intensity;
};

ODMRData odmrSpectrum[MW_STEPS];

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }  // Esperar conexión Serial
  
  // Configurar pines
  pinMode(LASER_PIN, OUTPUT);
  pinMode(LASER_PWM, OUTPUT);
  pinMode(MW_LE_PIN, OUTPUT);
  pinMode(MW_DATA_PIN, OUTPUT);
  pinMode(MW_CLK_PIN, OUTPUT);
  pinMode(LED_STATUS, OUTPUT);
  
  // Inicializar periféricos
  Wire.begin();
  
  // Inicializar ADC ADS1115
  if (!adc.begin()) {
    Serial.println("ERROR: No se pudo inicializar ADS1115");
    errorLoop();
  }
  adc.setGain(ADS1115_PGA_6P144);  // Rango ±6.144V
  adc.setDataRate(ADS1115_DR_860SPS);  // Máxima velocidad
  
  // Inicializar generador de microondas
  initMWGenerator();
  
  // Cargar calibración desde EEPROM (si existe)
  loadCalibration();
  
  // Señal de inicio
  digitalWrite(LED_STATUS, HIGH);
  delay(500);
  digitalWrite(LED_STATUS, LOW);
  
  Serial.println("{\"status\":\"ready\",\"message\":\"NV Sensor Initialized\"}");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  // Procesar comandos Serial
  if (Serial.available() > 0) {
    processCommand();
  }
  
  // Modo continuo (si está activado)
  if (continuousMode) {
    MeasurementResult result = performMeasurement();
    sendResultJSON(result);
    delay(100);  // 10 Hz
  }
}

// ==================== COMANDOS SERIAL ====================
bool continuousMode = false;

void processCommand() {
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  
  if (cmd == "MEASURE") {
    MeasurementResult result = performMeasurement();
    sendResultJSON(result);
  }
  else if (cmd == "START") {
    continuousMode = true;
    digitalWrite(LASER_PIN, HIGH);  // Encender láser
    Serial.println("{\"status\":\"started\"}");
  }
  else if (cmd == "STOP") {
    continuousMode = false;
    digitalWrite(LASER_PIN, LOW);   // Apagar láser
    Serial.println("{\"status\":\"stopped\"}");
  }
  else if (cmd == "CALIBRATE") {
    calibrateSensor();
  }
  else if (cmd == "SPECTRUM") {
    acquireFullSpectrum();
  }
  else if (cmd.startsWith("FREQ")) {
    float freq = cmd.substring(5).toFloat();
    setMWFrequency(freq);
    Serial.print("{\"frequency_set\":");
    Serial.print(freq);
    Serial.println("}");
  }
  else if (cmd == "HELP") {
    printHelp();
  }
}

void printHelp() {
  Serial.println("Comandos disponibles:");
  Serial.println("  MEASURE   - Realizar una medición");
  Serial.println("  START     - Iniciar modo continuo");
  Serial.println("  STOP      - Detener modo continuo");
  Serial.println("  CALIBRATE - Calibrar sensor");
  Serial.println("  SPECTRUM  - Adquirir espectro ODMR completo");
  Serial.println("  FREQ:<Hz> - Establecer frecuencia MW");
  Serial.println("  HELP      - Mostrar esta ayuda");
}

// ==================== MEDICIÓN PRINCIPAL ====================
struct MeasurementResult {
  float resonanceFreq;
  float magneticField;
  float contrast;
  unsigned long timestamp;
  bool valid;
};

MeasurementResult performMeasurement() {
  MeasurementResult result;
  result.timestamp = millis();
  result.valid = false;
  
  // Asegurar que láser está encendido
  digitalWrite(LASER_PIN, HIGH);
  delay(10);  // Estabilización
  
  // Realizar barrido ODMR
  float minIntensity = 1e9;
  float maxIntensity = 0;
  int minIndex = 0;
  
  for (int i = 0; i < MW_STEPS; i++) {
    float freq = MW_FREQ_CENTER - MW_FREQ_SPAN/2 + 
                 (MW_FREQ_SPAN * i / MW_STEPS);
    
    setMWFrequency(freq);
    delayMicroseconds(500);  // Tiempo de asentamiento
    
    // Promediar varias lecturas ADC
    long sum = 0;
    for (int j = 0; j < 10; j++) {
      sum += adc.readADC_SingleEnded(0);
    }
    float intensity = sum / 10.0;
    
    odmrSpectrum[i].frequency = freq;
    odmrSpectrum[i].intensity = intensity;
    
    if (intensity < minIntensity) {
      minIntensity = intensity;
      minIndex = i;
    }
    if (intensity > maxIntensity) {
      maxIntensity = intensity;
    }
  }
  
  // Calcular resultado
  result.resonanceFreq = odmrSpectrum[minIndex].frequency;
  result.contrast = (maxIntensity - minIntensity) / maxIntensity;
  result.magneticField = calculateMagneticField(result.resonanceFreq);
  result.valid = (result.contrast > 0.05);  // Mínimo 5% contraste
  
  return result;
}

float calculateMagneticField(float freq) {
  // f = f0 ± γ * B
  // B = (f - f0) / γ
  float deltaF = freq - MW_FREQ_CENTER;
  float field = deltaF / GAMMA_E;
  
  // Aplicar calibración
  field = (field - calibrationOffset) * calibrationScale;
  
  return field;
}

void sendResultJSON(MeasurementResult result) {
  Serial.print("{");
  Serial.print("\"timestamp\":"); Serial.print(result.timestamp);
  Serial.print(",\"frequency\":"); Serial.print(result.resonanceFreq, 3);
  Serial.print(",\"field_tesla\":"); Serial.print(result.magneticField, 9);
  Serial.print(",\"field_gauss\":"); Serial.print(result.magneticField * TESLA_TO_GAUSS, 5);
  Serial.print(",\"contrast\":"); Serial.print(result.contrast, 4);
  Serial.print(",\"valid\":"); Serial.print(result.valid ? "true" : "false");
  Serial.println("}");
}

// ==================== GENERADOR DE MICROONDAS (ADF4351) ====================
void initMWGenerator() {
  digitalWrite(MW_LE_PIN, HIGH);
  delay(10);
  
  // Configuración inicial del ADF4351
  // Registros para frecuencia central (2.87 GHz)
  writeADF4351Register(0x00580000);  // Register 5
  writeADF4351Register(0x008C8024);  // Register 4
  writeADF4351Register(0x000004B3);  // Register 3
  writeADF4351Register(0x00004E42);  // Register 2
  writeADF4351Register(0x08008011);  // Register 1
  writeADF4351Register(0x004F8018);  // Register 0 (2.87 GHz)
}

void setMWFrequency(float freq) {
  // Calcular valores de registro para frecuencia objetivo
  // Implementación simplificada - ver datasheet ADF4351
  
  float PFD = 25e6;  // Frecuencia de referencia
  int R = 1;         // Prescaler
  int INT = (int)(freq / PFD);
  int FRAC = (int)((freq / PFD - INT) * 4096);
  
  // Construir registro 0
  uint32_t reg0 = (INT << 15) | (FRAC << 3);
  writeADF4351Register(reg0);
}

void writeADF4351Register(uint32_t data) {
  digitalWrite(MW_LE_PIN, LOW);
  
  for (int i = 31; i >= 0; i--) {
    digitalWrite(MW_DATA_PIN, (data >> i) & 0x01);
    digitalWrite(MW_CLK_PIN, HIGH);
    delayMicroseconds(1);
    digitalWrite(MW_CLK_PIN, LOW);
    delayMicroseconds(1);
  }
  
  digitalWrite(MW_LE_PIN, HIGH);
  delayMicroseconds(10);
}

// ==================== CALIBRACIÓN ====================
void calibrateSensor() {
  Serial.println("{\"status\":\"calibrating\"}");
  
  // Tomar múltiples mediciones para promediar
  float sum = 0;
  int validCount = 0;
  
  for (int i = 0; i < 100; i++) {
    MeasurementResult r = performMeasurement();
    if (r.valid) {
      sum += r.magneticField;
      validCount++;
    }
    delay(50);
  }
  
  if (validCount > 50) {
    calibrationOffset = sum / validCount;  // Asumir campo ~0 en promedio
    saveCalibration();
    Serial.print("{\"status\":\"calibrated\",\"offset\":");
    Serial.print(calibrationOffset, 9);
    Serial.println("}");
  } else {
    Serial.println("{\"status\":\"error\",\"message\":\"Calibration failed\"}");
  }
}

void saveCalibration() {
  // Guardar en EEPROM (implementar según plataforma)
  // EEPROM.put(0, calibrationOffset);
  // EEPROM.put(4, calibrationScale);
}

void loadCalibration() {
  // Cargar desde EEPROM
  // EEPROM.get(0, calibrationOffset);
  // EEPROM.get(4, calibrationScale);
}

// ==================== ESPECTRO COMPLETO ====================
void acquireFullSpectrum() {
  Serial.println("{\"spectrum_start\":true}");
  
  for (int i = 0; i < MW_STEPS; i++) {
    Serial.print("{\"i\":"); Serial.print(i);
    Serial.print(",\"f\":"); Serial.print(odmrSpectrum[i].frequency, 3);
    Serial.print(",\"int\":"); Serial.print(odmrSpectrum[i].intensity, 2);
    Serial.println("}");
  }
  
  Serial.println("{\"spectrum_end\":true}");
}

// ==================== UTILIDADES ====================
void errorLoop() {
  while (1) {
    digitalWrite(LED_STATUS, HIGH);
    delay(100);
    digitalWrite(LED_STATUS, LOW);
    delay(100);
  }
}
