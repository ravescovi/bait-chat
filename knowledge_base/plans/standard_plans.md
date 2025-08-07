# Standard Bluesky Scan Plans

This document provides detailed information about the standard scan plans available in the bAIt-Chat system.

## Core Scan Plans

### scan(detectors, motor, start, stop, num)

**Purpose**: Perform a continuous scan by moving a motor from start to stop position while collecting data from detectors at regular intervals.

**How it works**:
1. The motor moves continuously from the start position to the stop position
2. Detectors collect data at evenly spaced intervals during the movement
3. The number of data points is specified by the `num` parameter
4. Data collection is synchronized with motor position

**Parameters**:
- `detectors`: List of detector objects to read from (e.g., `[pilatus, i0]`)
- `motor`: Motor object to move (e.g., `motor_x`, `motor_theta`)
- `start`: Starting position in motor units (mm, degrees, etc.)
- `stop`: Ending position in motor units
- `num`: Number of data points to collect

**Example Usage**:
```python
# X-ray diffraction scan across sample
scan([pilatus, i0], motor_x, 0, 5, 51)

# Rotation scan for texture analysis
scan([pilatus], motor_theta, 0, 180, 181)

# Energy scan using monochromator
scan([i0, it], mono_energy, 8900, 9100, 201)
```

**Typical Use Cases**:
- Absorption edge scans (XANES/EXAFS)
- Powder diffraction mapping
- Sample characterization
- Beam alignment procedures
- Temperature or pressure dependent studies

---

### count(detectors, num=1, delay=None)

**Purpose**: Take repeated measurements at the current position to improve counting statistics or monitor stability over time.

**How it works**:
1. All motors remain at their current positions
2. Detectors collect data for the specified number of readings
3. Optional delay between measurements for time-resolved studies
4. Results can be averaged or analyzed for stability

**Parameters**:
- `detectors`: List of detector objects (e.g., `[pilatus, i0, it]`)
- `num`: Number of measurements to take (default: 1)
- `delay`: Time between measurements in seconds (optional)

**Example Usage**:
```python
# Single measurement for alignment check
count([pilatus, i0])

# Statistical improvement with 10 measurements
count([pilatus, i0], num=10)

# Time series with 1-second intervals
count([i0, it], num=60, delay=1.0)

# Long exposure for weak signals
count([pilatus], num=1)  # Use detector's configured exposure time
```

**Typical Use Cases**:
- Beam intensity monitoring
- Detector calibration
- Statistical improvement of weak signals
- Stability monitoring
- Quick alignment checks

---

### list_scan(detectors, motor, positions)

**Purpose**: Move to specific positions from a predefined list and collect data at each point.

**How it works**:
1. The motor moves to each position in the provided list sequentially
2. At each position, the system waits for motor settling
3. Data is collected from all specified detectors
4. Process repeats for all positions in the list

**Parameters**:
- `detectors`: List of detector objects
- `motor`: Motor object to move
- `positions`: List of specific positions to visit (e.g., `[0, 1.5, 3.2, 5.0]`)

**Example Usage**:
```python
# Measure at specific points of interest
list_scan([pilatus], motor_x, [0, 1.5, 3.2, 5.0])

# Angular positions for texture analysis
angles = [0, 15, 30, 45, 60, 75, 90]
list_scan([pilatus], motor_theta, angles)

# Energy points around absorption edge
energies = [8970, 8979, 8990, 9000, 9010, 9020]
list_scan([i0, it], mono_energy, energies)
```

**Typical Use Cases**:
- Measuring at predetermined points of interest
- Returning to previously identified features
- Non-uniform sampling (e.g., more points near edges)
- Following up on anomalies found in continuous scans

---

### grid_scan(detectors, motor1, start1, stop1, num1, motor2, start2, stop2, num2, snake=True)

**Purpose**: Perform a 2D scan over two motors to create a map or image of the sample.

**How it works**:
1. Creates a rectangular grid of measurement points
2. Can use "snake" pattern for efficient scanning (recommended)
3. Collects data from detectors at each grid point
4. Results can be visualized as 2D images or heatmaps

**Parameters**:
- `detectors`: List of detector objects
- `motor1`, `motor2`: Two motor objects for the scan axes
- `start1`, `stop1`, `num1`: Parameters for first motor axis
- `start2`, `stop2`, `num2`: Parameters for second motor axis
- `snake`: Use snake pattern for efficiency (default: True)

**Example Usage**:
```python
# 2D sample mapping
grid_scan([pilatus], motor_x, -2, 2, 21, motor_y, -1, 1, 11)

# High-resolution area scan
grid_scan([pilatus, i0], motor_x, 0, 1, 51, motor_y, 0, 1, 51, snake=True)
```

**Typical Use Cases**:
- Sample mapping and characterization
- Finding optimal measurement positions
- Studying spatial variations in samples
- Creating diffraction or absorption maps

---

### fly_scan(detectors, motor, start, stop, num, exposure_time)

**Purpose**: High-speed continuous data acquisition while motor moves at constant velocity.

**How it works**:
1. Motor accelerates to constant velocity
2. Data collection triggered at regular time intervals during motion
3. Much faster than step-scan approaches
4. Requires hardware triggering capabilities

**Parameters**:
- `detectors`: List of detectors (must support hardware triggering)
- `motor`: Motor object (must support constant velocity mode)
- `start`, `stop`: Position range
- `num`: Number of data points
- `exposure_time`: Detector exposure time per point

**Example Usage**:
```python
# Fast diffraction scan
fly_scan([pilatus], motor_theta, 0, 90, 900, 0.1)

# Quick sample survey
fly_scan([i0, it], motor_x, -5, 5, 100, 0.05)
```

**Typical Use Cases**:
- Time-critical measurements
- Large area surveys
- High-throughput screening
- Real-time process monitoring

---

## Specialized Plans

### rel_scan(detectors, motor, start, stop, num)

**Purpose**: Relative scan around the current motor position.

**Parameters are relative to current position**:
- Actual start = current_position + start
- Actual stop = current_position + stop

**Example**:
```python
# Scan ±1mm around current position
rel_scan([pilatus], motor_x, -1, 1, 21)
```

### log_scan(detectors, motor, start, stop, num)

**Purpose**: Logarithmic spacing of measurement points.

**Use Cases**:
- EXAFS scans (logarithmic k-space)
- Wide dynamic range measurements

### spiral(detectors, x_motor, y_motor, x_range, y_range, dr)

**Purpose**: Spiral pattern scan for efficient 2D coverage.

**Use Cases**:
- Finding small features
- Efficient 2D searches
- Beam centering procedures

---

## Plan Combinations and Sequences

### Adaptive Scanning

Plans can be combined with adaptive logic:

```python
# First do a coarse scan
coarse_result = scan([i0], motor_x, 0, 10, 11)

# Find peak position and do fine scan around it
peak_pos = find_peak(coarse_result)
fine_result = scan([pilatus], motor_x, peak_pos-0.5, peak_pos+0.5, 51)
```

### Multi-Step Procedures

Common multi-step measurement procedures:

1. **Alignment Sequence**:
   - Coarse alignment scan
   - Peak finding
   - Fine alignment scan
   - Final position optimization

2. **Full Characterization**:
   - Quick survey scan
   - Detailed measurement at points of interest
   - Background measurements
   - Reference measurements

---

## Best Practices

### Motor Selection
- Use appropriate motor for the measurement type
- Consider resolution and range requirements
- Account for mechanical settling time

### Detector Configuration
- Match exposure times to count rates
- Consider detector readout time
- Use appropriate triggering modes

### Scan Parameters
- Choose step size based on feature size
- Balance measurement time vs. resolution
- Consider beam damage for sensitive samples

### Data Quality
- Include reference measurements
- Monitor beam stability (I0)
- Account for detector dark current
- Consider background subtraction

### Safety Considerations
- Check motor limits before scanning
- Monitor sample for beam damage
- Use appropriate exposure times
- Implement safety interlocks

---

## Common Parameter Combinations

### Powder Diffraction
```python
# Standard powder pattern
scan([pilatus], motor_theta, 5, 85, 801)

# High-resolution pattern
scan([pilatus], motor_theta, 10, 50, 4001)
```

### Absorption Spectroscopy
```python
# XANES scan
scan([i0, it], mono_energy, 8900, 9100, 201)

# EXAFS scan (requires log spacing)
log_scan([i0, it], mono_energy, 9100, 9800, 500)
```

### Sample Characterization
```python
# Position optimization
scan([i0], motor_x, -2, 2, 41)
scan([i0], motor_y, -1, 1, 21)

# 2D mapping
grid_scan([pilatus], motor_x, -1, 1, 21, motor_y, -1, 1, 21)
```