import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/projwt_provider.dart';

class SummonScreen extends StatefulWidget {
  const SummonScreen({Key? key}) : super(key: key);

  @override
  State<SummonScreen> createState() => _SummonScreenState();
}

class _SummonScreenState extends State<SummonScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  double _carX = 50; // percentage
  double _carY = 50; // percentage
  double _speed = 0; // mph
  bool _isSimulating = false;
  String _currentState = 'IDLE';

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 50),
      vsync: this,
    );
    _animationController.addListener(_updateSimulation);
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _updateSimulation() {
    if (!_isSimulating) return;

    setState(() {
      // Simple autonomous path: move right then down
      if (_carX < 80) {
        _carX += 0.5;
        _speed = 15;
      } else if (_carY < 80) {
        _carY += 0.5;
        _speed = 15;
      } else {
        _isSimulating = false;
        _speed = 0;
        _currentState = 'COMPLETED';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ProjWTProvider>(
      builder: (context, provider, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Summon Info Card
              _buildSummonInfoCard(context),
              const SizedBox(height: 16),

              // Simulation Canvas
              _buildSimulationCanvas(context),
              const SizedBox(height: 24),

              // State Machine Diagram
              _buildStateMachineDiagram(context),
              const SizedBox(height: 24),

              // Control Panel
              _buildControlPanel(context, provider),
              const SizedBox(height: 24),

              // Safety Features
              _buildSafetyFeatures(context),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSummonInfoCard(BuildContext context) {
    return Card(
      color: Colors.purple.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Autonomous Summon Simulation',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Watch the car navigate autonomously using the fail-closed safety state machine. Press PANIC at any time to emergency-stop.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Chip(
              icon: const Icon(Icons.info),
              label: const Text('DEMO ONLY — Not real vehicle control'),
              backgroundColor: Colors.amber.withOpacity(0.2),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSimulationCanvas(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Canvas
            Container(
              width: double.infinity,
              height: 300,
              decoration: BoxDecoration(
                color: Colors.grey[100],
                border: Border.all(color: Colors.grey[300]!),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Stack(
                children: [
                  // Grid background
                  Positioned.fill(
                    child: CustomPaint(
                      painter: GridPainter(),
                    ),
                  ),

                  // Start point
                  Positioned(
                    left: 20,
                    top: MediaQuery.of(context).size.width * 0.15 - 24,
                    child: Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.green,
                      ),
                      child: const Icon(Icons.location_on,
                          size: 14, color: Colors.white),
                    ),
                  ),

                  // Destination
                  Positioned(
                    right: 20,
                    bottom: 20,
                    child: Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.red,
                      ),
                      child: const Icon(Icons.location_on,
                          size: 14, color: Colors.white),
                    ),
                  ),

                  // Car
                  Positioned(
                    left: (MediaQuery.of(context).size.width - 32) * _carX / 100,
                    top: 280 * _carY / 100,
                    child: Container(
                      width: 32,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.blue,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.directions_car,
                              size: 24, color: Colors.white),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 12),

            // Telemetry
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildTelemetryBox('Speed', '$_speed mph'),
                _buildTelemetryBox('Position', '${_carX.toStringAsFixed(0)}%, ${_carY.toStringAsFixed(0)}%'),
                _buildTelemetryBox('State', _currentState),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTelemetryBox(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildStateMachineDiagram(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Safety State Machine',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 16),

            // State diagram
            Column(
              children: [
                _buildStateBox('IDLE', _currentState == 'IDLE'),
                _buildArrow('ARM'),
                _buildStateBox('ARMED', _currentState == 'ARMED'),
                _buildArrow('SUMMON'),
                _buildStateBox('MOVING', _currentState == 'MOVING' || _isSimulating),
                _buildArrow('REACHED'),
                _buildStateBox('COMPLETED', _currentState == 'COMPLETED'),
                const SizedBox(height: 16),
                _buildArrow('PANIC (from any state)', isWarning: true),
                _buildStateBox('EMERGENCY STOP', false),
              ],
            ),

            const SizedBox(height: 12),

            // Explanation
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                '• IDLE: No commands accepted\n'
                '• ARMED: Ready for summon\n'
                '• MOVING: Autonomous navigation in progress\n'
                '• PANIC: Emergency stop cuts all control\n'
                '• Auto-disarm after 15s of inactivity',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStateBox(String state, bool isActive) {
    final color = isActive ? Colors.green : Colors.grey[300];
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: color == Colors.green ? Colors.green : Colors.grey[400]!,
          width: 2,
        ),
      ),
      child: Text(
        state,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontWeight: FontWeight.bold,
          color: color == Colors.green ? Colors.white : Colors.black,
        ),
      ),
    );
  }

  Widget _buildArrow(String label, {bool isWarning = false}) {
    return Column(
      children: [
        Icon(Icons.arrow_downward,
            color: isWarning ? Colors.red : Colors.grey[400]),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: isWarning ? Colors.red : Colors.grey,
          ),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _buildControlPanel(BuildContext context, ProjWTProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Simulation Controls',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _isSimulating ? null : _startSummon,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start Summon'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _stopSummon,
                icon: const Icon(Icons.stop),
                label: const Text('Stop'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _resetSimulation,
            icon: const Icon(Icons.refresh),
            label: const Text('Reset'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSafetyFeatures(BuildContext context) {
    return Card(
      color: Colors.orange.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Safety Features',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            _buildSafetyFeature('Fail-Closed', 'Default state is IDLE (disarmed)'),
            _buildSafetyFeature('Emergency Override', 'PANIC stops all motion immediately'),
            _buildSafetyFeature('Auto-Disarm', 'System disarms after 15 seconds inactivity'),
            _buildSafetyFeature('Command Gating', 'Only armed state accepts commands'),
          ],
        ),
      ),
    );
  }

  Widget _buildSafetyFeature(String title, String description) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle, color: Colors.green, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(description,
                    style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _startSummon() {
    setState(() {
      _isSimulating = true;
      _currentState = 'ARMED';
    });
    _animationController.repeat();
  }

  void _stopSummon() {
    setState(() {
      _isSimulating = false;
      _currentState = 'IDLE';
      _speed = 0;
    });
    _animationController.stop();
  }

  void _resetSimulation() {
    setState(() {
      _carX = 50;
      _carY = 50;
      _speed = 0;
      _isSimulating = false;
      _currentState = 'IDLE';
    });
    _animationController.stop();
  }
}

class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey.withOpacity(0.2)
      ..strokeWidth = 0.5;

    const spacing = 20.0;

    // Vertical lines
    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }

    // Horizontal lines
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(GridPainter oldDelegate) => false;
}
